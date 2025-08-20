from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional, Tuple
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid
import re

from ..models import Transfer, TransferStatusHistory, ExchangeRateSnapshot, Client
from .fx import FXService


class TransferService:
    """Serviço para gerenciar transferências de dinheiro"""
    
    # Configurações do serviço
    MIN_TRANSFER_AMOUNT = Decimal('10.00')  # USD
    MAX_TRANSFER_AMOUNT = Decimal('10000.00')  # USD
    SERVICE_FEE_PERCENTAGE = Decimal('0.02')  # 2%
    MIN_SERVICE_FEE = Decimal('2.00')  # USD
    EXCHANGE_RATE_SPREAD = Decimal('0.015')  # 1.5%
    
    def __init__(self):
        self.fx_service = FXService()
    
    def validate_transfer_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Valida os dados de uma transferência"""
        errors = {}
        
        # Validar valor
        try:
            amount_usd = Decimal(str(data.get('amount_usd', 0)))
            if amount_usd < self.MIN_TRANSFER_AMOUNT:
                errors['amount_usd'] = f'Valor mínimo é ${self.MIN_TRANSFER_AMOUNT}'
            elif amount_usd > self.MAX_TRANSFER_AMOUNT:
                errors['amount_usd'] = f'Valor máximo é ${self.MAX_TRANSFER_AMOUNT}'
        except (ValueError, TypeError):
            errors['amount_usd'] = 'Valor inválido'
        
        # Validar nome do beneficiário
        beneficiary_name = data.get('beneficiary_name', '').strip()
        if not beneficiary_name:
            errors['beneficiary_name'] = 'Nome do beneficiário é obrigatório'
        elif len(beneficiary_name) < 2:
            errors['beneficiary_name'] = 'Nome deve ter pelo menos 2 caracteres'
        elif len(beneficiary_name) > 120:
            errors['beneficiary_name'] = 'Nome muito longo (máximo 120 caracteres)'
        
        # Validar CPF
        cpf = data.get('beneficiary_cpf', '').strip()
        if not cpf:
            errors['beneficiary_cpf'] = 'CPF é obrigatório'
        elif not self._validate_cpf(cpf):
            errors['beneficiary_cpf'] = 'CPF inválido'
        
        # Validar chave PIX
        pix_key = data.get('pix_key', '').strip()
        if not pix_key:
            errors['pix_key'] = 'Chave PIX é obrigatória'
        elif not self._validate_pix_key(pix_key):
            errors['pix_key'] = 'Chave PIX inválida'
        
        return errors
    
    def _validate_cpf(self, cpf: str) -> bool:
        """Valida um CPF brasileiro"""
        # Remove caracteres não numéricos
        cpf = re.sub(r'\D', '', cpf)
        
        # Verifica se tem 11 dígitos
        if len(cpf) != 11:
            return False
        
        # Verifica se não são todos os dígitos iguais
        if cpf == cpf[0] * 11:
            return False
        
        # Calcula o primeiro dígito verificador
        sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digit1 = 11 - (sum1 % 11)
        if digit1 >= 10:
            digit1 = 0
        
        # Calcula o segundo dígito verificador
        sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digit2 = 11 - (sum2 % 11)
        if digit2 >= 10:
            digit2 = 0
        
        # Verifica se os dígitos calculados conferem
        return cpf[-2:] == f"{digit1}{digit2}"
    
    def _validate_pix_key(self, pix_key: str) -> bool:
        """Valida uma chave PIX"""
        pix_key = pix_key.strip()
        
        # CPF (11 dígitos)
        if re.match(r'^\d{11}$', pix_key):
            return self._validate_cpf(pix_key)
        
        # CNPJ (14 dígitos)
        if re.match(r'^\d{14}$', pix_key):
            return True  # Simplificado - poderia validar CNPJ completo
        
        # Email
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', pix_key):
            return True
        
        # Telefone (+5511999999999)
        if re.match(r'^\+55\d{10,11}$', pix_key):
            return True
        
        # Chave aleatória (UUID)
        try:
            uuid.UUID(pix_key)
            return True
        except ValueError:
            pass
        
        return False
    
    def calculate_transfer_amounts(self, amount_usd: Decimal) -> Dict[str, Decimal]:
        """Calcula os valores da transferência incluindo taxas e câmbio"""
        # Obter taxa de câmbio atual
        exchange_data = self.fx_service.get_usd_to_brl_rate()
        if not exchange_data['success']:
            raise ValidationError('Não foi possível obter a taxa de câmbio atual')
        
        base_rate = Decimal(str(exchange_data['rate']))
        
        # Aplicar spread na taxa de câmbio
        spread_amount = base_rate * self.EXCHANGE_RATE_SPREAD
        final_rate = base_rate - spread_amount  # Taxa menor para o cliente
        
        # Calcular taxa de serviço
        service_fee = amount_usd * self.SERVICE_FEE_PERCENTAGE
        if service_fee < self.MIN_SERVICE_FEE:
            service_fee = self.MIN_SERVICE_FEE
        
        # Valores finais
        total_amount_usd = amount_usd + service_fee
        amount_brl_estimated = amount_usd * final_rate
        
        # Arredondar valores
        service_fee = service_fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_amount_usd = total_amount_usd.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        amount_brl_estimated = amount_brl_estimated.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        final_rate = final_rate.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
        
        return {
            'base_rate': base_rate,
            'final_rate': final_rate,
            'spread_percentage': self.EXCHANGE_RATE_SPREAD,
            'service_fee': service_fee,
            'total_amount_usd': total_amount_usd,
            'amount_brl_estimated': amount_brl_estimated,
            'rate_source': exchange_data.get('source', 'unknown')
        }
    
    @transaction.atomic
    def create_transfer(self, client: Client, transfer_data: Dict[str, Any]) -> Tuple[Transfer, Dict[str, str]]:
        """Cria uma nova transferência"""
        # Validar dados
        errors = self.validate_transfer_data(transfer_data)
        if errors:
            return None, errors
        
        try:
            amount_usd = Decimal(str(transfer_data['amount_usd']))
            
            # Calcular valores
            calculations = self.calculate_transfer_amounts(amount_usd)
            
            # Criar transferência
            transfer = Transfer.objects.create(
                client=client,
                beneficiary_name=transfer_data['beneficiary_name'].strip(),
                beneficiary_cpf=re.sub(r'\D', '', transfer_data['beneficiary_cpf']),
                pix_key=transfer_data['pix_key'].strip(),
                beneficiary_address=transfer_data.get('beneficiary_address', '').strip(),
                amount_usd=amount_usd,
                exchange_rate=calculations['final_rate'],
                service_fee=calculations['service_fee'],
                total_amount_usd=calculations['total_amount_usd'],
                amount_brl_estimated=calculations['amount_brl_estimated'],
                status='draft'
            )
            
            # Criar snapshot da taxa de câmbio
            ExchangeRateSnapshot.objects.create(
                transfer=transfer,
                usd_to_brl_rate=calculations['base_rate'],
                rate_source=calculations['rate_source'],
                rate_timestamp=timezone.now(),
                spread_percentage=calculations['spread_percentage'],
                final_rate=calculations['final_rate']
            )
            
            # Registrar histórico de status
            self._add_status_history(transfer, '', 'draft', 'system', 'Transferência criada')
            
            return transfer, {}
            
        except Exception as e:
            return None, {'general': f'Erro ao criar transferência: {str(e)}'}
    
    @transaction.atomic
    def update_transfer_status(self, transfer: Transfer, new_status: str, 
                             changed_by: str = 'system', notes: str = '') -> bool:
        """Atualiza o status de uma transferência"""
        if new_status not in dict(Transfer.STATUS_CHOICES):
            raise ValidationError(f'Status inválido: {new_status}')
        
        previous_status = transfer.status
        transfer.status = new_status
        
        # Atualizar timestamps específicos
        if new_status == 'payment_confirmed':
            transfer.payment_confirmed_at = timezone.now()
        elif new_status == 'completed':
            transfer.completed_at = timezone.now()
        
        transfer.save()
        
        # Registrar histórico
        self._add_status_history(transfer, previous_status, new_status, changed_by, notes)
        
        return True
    
    def _add_status_history(self, transfer: Transfer, previous_status: str, 
                          new_status: str, changed_by: str, notes: str = ''):
        """Adiciona entrada no histórico de status"""
        TransferStatusHistory.objects.create(
            transfer=transfer,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=changed_by,
            notes=notes
        )
    
    def get_transfer_by_id(self, transfer_id: str) -> Optional[Transfer]:
        """Busca uma transferência pelo ID"""
        try:
            return Transfer.objects.select_related('client', 'rate_snapshot').get(
                transfer_id=transfer_id
            )
        except Transfer.DoesNotExist:
            return None
    
    def get_client_transfers(self, client: Client, status: str = None) -> list:
        """Busca transferências de um cliente"""
        queryset = Transfer.objects.filter(client=client).select_related('rate_snapshot')
        
        if status:
            queryset = queryset.filter(status=status)
        
        return list(queryset.order_by('-created_at'))
    
    def generate_payment_link(self, transfer: Transfer) -> str:
        """Gera link de pagamento para uma transferência"""
        from .payments import create_payment_link
        
        payment_data = {
            'amount': float(transfer.total_amount_usd),
            'currency': 'USD',
            'description': f'Transferência {transfer.transfer_id}',
            'metadata': {
                'transfer_id': transfer.transfer_id,
                'client_id': str(transfer.client.id),
                'beneficiary_name': transfer.beneficiary_name
            }
        }
        
        result = create_payment_link(payment_data)
        if result['success']:
            # Atualizar a transferência com o link e referência
            transfer.payment_link = result['payment_url']
            transfer.payment_reference = result['payment_id']
            transfer.save()
            return result['payment_url']
        else:
            raise ValidationError(f'Erro ao gerar link de pagamento: {result["error"]}')
    
    def get_transfer_summary(self, transfer: Transfer) -> Dict[str, Any]:
        """Retorna um resumo completo da transferência"""
        return {
            'transfer_id': transfer.transfer_id,
            'status': transfer.status,
            'status_display': transfer.get_status_display(),
            'client': {
                'name': transfer.client.name,
                'phone': transfer.client.phone
            },
            'beneficiary': {
                'name': transfer.beneficiary_name,
                'cpf': transfer.beneficiary_cpf,
                'pix_key': transfer.pix_key,
                'address': transfer.beneficiary_address
            },
            'amounts': {
                'amount_usd': float(transfer.amount_usd),
                'service_fee': float(transfer.service_fee),
                'total_amount_usd': float(transfer.total_amount_usd),
                'exchange_rate': float(transfer.exchange_rate),
                'amount_brl_estimated': float(transfer.amount_brl_estimated),
                'amount_brl_final': float(transfer.amount_brl_final) if transfer.amount_brl_final else None
            },
            'payment': {
                'method': transfer.payment_method,
                'reference': transfer.payment_reference,
                'link': transfer.payment_link
            },
            'timestamps': {
                'created_at': transfer.created_at.isoformat(),
                'updated_at': transfer.updated_at.isoformat(),
                'payment_confirmed_at': transfer.payment_confirmed_at.isoformat() if transfer.payment_confirmed_at else None,
                'completed_at': transfer.completed_at.isoformat() if transfer.completed_at else None
            },
            'notes': transfer.notes,
            'external_reference': transfer.external_reference
        }