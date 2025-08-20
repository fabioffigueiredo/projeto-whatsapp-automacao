import hashlib
import hmac
import logging
from django.conf import settings
from django.http import HttpRequest
from decimal import Decimal
import requests
import json
from typing import Dict, Optional
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class PaymentProvider:
    """
    Classe base para provedores de pagamento
    """
    def create_payment_link(self, transfer_id: int, amount_usd: Decimal, customer_data: Dict) -> str:
        raise NotImplementedError
    
    def verify_payment(self, payment_id: str) -> Dict:
        raise NotImplementedError

class StripeProvider(PaymentProvider):
    """
    Integração com Stripe
    """
    def __init__(self):
        self.api_key = settings.PAYMENT_SECRET_KEY
        self.publishable_key = settings.PAYMENT_API_KEY
    
    def create_payment_link(self, transfer_id: int, amount_usd: Decimal, customer_data: Dict) -> str:
        try:
            import stripe
            stripe.api_key = self.api_key
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'Transferência Internacional - ID {transfer_id}',
                            'description': f'Envio de ${amount_usd} para {customer_data.get("beneficiary_name", "destinatário")}'
                        },
                        'unit_amount': int(amount_usd * 100),  # Stripe usa centavos
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=settings.PAYMENT_SUCCESS_URL + f'?transfer_id={transfer_id}',
                cancel_url=settings.PAYMENT_CANCEL_URL + f'?transfer_id={transfer_id}',
                metadata={'transfer_id': str(transfer_id)},
                customer_email=customer_data.get('email'),
                expires_at=int((timezone.now() + timedelta(minutes=30)).timestamp())  # Expira em 30 minutos
            )
            
            logger.info(f"Stripe payment session created for transfer {transfer_id}: {session.id}")
            return session.url
            
        except Exception as e:
            logger.error(f"Error creating Stripe payment link for transfer {transfer_id}: {e}")
            raise
    
    def verify_payment(self, payment_id: str) -> Dict:
        try:
            import stripe
            stripe.api_key = self.api_key
            
            session = stripe.checkout.Session.retrieve(payment_id)
            return {
                'status': session.payment_status,
                'amount': session.amount_total / 100,  # Converter de centavos
                'currency': session.currency,
                'metadata': session.metadata
            }
        except Exception as e:
            logger.error(f"Error verifying Stripe payment {payment_id}: {e}")
            return {'status': 'error', 'error': str(e)}

class MercadoPagoProvider(PaymentProvider):
    """
    Integração com MercadoPago
    """
    def __init__(self):
        self.access_token = settings.PAYMENT_SECRET_KEY
        self.base_url = "https://api.mercadopago.com"
    
    def create_payment_link(self, transfer_id: int, amount_usd: Decimal, customer_data: Dict) -> str:
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'items': [{
                    'title': f'Transferência Internacional - ID {transfer_id}',
                    'description': f'Envio de ${amount_usd} para {customer_data.get("beneficiary_name", "destinatário")}',
                    'quantity': 1,
                    'currency_id': 'USD',
                    'unit_price': float(amount_usd)
                }],
                'back_urls': {
                    'success': settings.PAYMENT_SUCCESS_URL + f'?transfer_id={transfer_id}',
                    'failure': settings.PAYMENT_CANCEL_URL + f'?transfer_id={transfer_id}',
                    'pending': settings.PAYMENT_CANCEL_URL + f'?transfer_id={transfer_id}'
                },
                'auto_return': 'approved',
                'external_reference': str(transfer_id),
                'notification_url': settings.PAYMENT_WEBHOOK_URL,
                'expires': True,
                'expiration_date_from': timezone.now().isoformat(),
                'expiration_date_to': (timezone.now() + timedelta(minutes=30)).isoformat()
            }
            
            if customer_data.get('email'):
                data['payer'] = {'email': customer_data['email']}
            
            response = requests.post(
                f'{self.base_url}/checkout/preferences',
                headers=headers,
                json=data
            )
            
            if response.status_code == 201:
                preference = response.json()
                logger.info(f"MercadoPago preference created for transfer {transfer_id}: {preference['id']}")
                return preference['init_point']
            else:
                logger.error(f"MercadoPago API error: {response.status_code} - {response.text}")
                raise Exception(f"MercadoPago API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error creating MercadoPago payment link for transfer {transfer_id}: {e}")
            raise
    
    def verify_payment(self, payment_id: str) -> Dict:
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(
                f'{self.base_url}/v1/payments/{payment_id}',
                headers=headers
            )
            
            if response.status_code == 200:
                payment = response.json()
                return {
                    'status': payment['status'],
                    'amount': payment['transaction_amount'],
                    'currency': payment['currency_id'],
                    'external_reference': payment.get('external_reference')
                }
            else:
                logger.error(f"MercadoPago payment verification error: {response.status_code}")
                return {'status': 'error', 'error': f"API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error verifying MercadoPago payment {payment_id}: {e}")
            return {'status': 'error', 'error': str(e)}

def get_payment_provider() -> PaymentProvider:
    """
    Retorna o provedor de pagamento configurado
    """
    provider_name = getattr(settings, 'PAYMENT_PROVIDER', 'stripe').lower()
    
    if provider_name == 'stripe':
        return StripeProvider()
    elif provider_name == 'mercadopago':
        return MercadoPagoProvider()
    else:
        raise ValueError(f"Provedor de pagamento não suportado: {provider_name}")

def create_payment_link(transfer_id: int, amount_usd: Decimal, customer_data: Optional[Dict] = None) -> str:
    """
    Cria um link de pagamento para a transferência
    """
    if customer_data is None:
        customer_data = {}
    
    # Se não há configuração de pagamento, retorna link simulado
    if not getattr(settings, 'PAYMENT_API_KEY', None):
        logger.warning("Payment provider not configured, returning simulated link")
        return f"https://payment-simulator.com/pay?transfer_id={transfer_id}&amount={amount_usd}"
    
    try:
        provider = get_payment_provider()
        return provider.create_payment_link(transfer_id, amount_usd, customer_data)
    except Exception as e:
        logger.error(f"Error creating payment link: {e}")
        # Fallback para link simulado em caso de erro
        return f"https://payment-simulator.com/pay?transfer_id={transfer_id}&amount={amount_usd}"


def verify_webhook_signature(request: HttpRequest) -> bool:
    """
    Verifica a assinatura HMAC do webhook de pagamento
    
    Args:
        request: Objeto HttpRequest do Django
    
    Returns:
        bool: True se a assinatura for válida, False caso contrário
    """
    try:
        # Obter o secret do webhook das configurações
        webhook_secret = getattr(settings, 'PAYMENT_WEBHOOK_SECRET', None)
        if not webhook_secret:
            logger.warning("PAYMENT_WEBHOOK_SECRET not configured, skipping signature verification")
            return True  # Em desenvolvimento, permite sem verificação
        
        # Obter a assinatura do header
        signature_header = request.headers.get('X-Signature') or request.headers.get('X-Hub-Signature-256')
        if not signature_header:
            logger.warning("No signature header found in payment webhook")
            return False
        
        # Extrair a assinatura (remover prefixo se existir)
        if signature_header.startswith('sha256='):
            signature = signature_header[7:]
        else:
            signature = signature_header
        
        # Calcular a assinatura esperada
        body = request.body
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Comparar as assinaturas de forma segura
        is_valid = hmac.compare_digest(signature, expected_signature)
        
        if not is_valid:
            logger.warning(f"Invalid webhook signature. Expected: {expected_signature}, Got: {signature}")
        
        return is_valid
        
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False


def get_payment_status(payment_id: str) -> Dict:
    """
    Consulta o status de um pagamento no provedor
    
    Args:
        payment_id (str): ID do pagamento no provedor
    
    Returns:
        dict: Status do pagamento
    """
    # Se não há configuração de pagamento, retorna status simulado
    if not getattr(settings, 'PAYMENT_API_KEY', None):
        logger.warning("Payment provider not configured, returning simulated status")
        return {
            'status': 'pending',
            'amount': 0,
            'currency': 'USD'
        }
    
    try:
        provider = get_payment_provider()
        return provider.verify_payment(payment_id)
    except Exception as e:
        logger.error(f"Error getting payment status: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }