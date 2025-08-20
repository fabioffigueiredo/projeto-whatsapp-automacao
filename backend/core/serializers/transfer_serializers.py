from rest_framework import serializers
from decimal import Decimal
import re

from ..models import Transfer, TransferStatusHistory, ExchangeRateSnapshot
from ..services.transfer_service import TransferService


class TransferCreateSerializer(serializers.Serializer):
    """Serializer para criação de transferências"""
    
    amount_usd = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2,
        min_value=Decimal('10.00'),
        max_value=Decimal('10000.00'),
        help_text="Valor em USD (mínimo $10, máximo $10,000)"
    )
    
    beneficiary_name = serializers.CharField(
        max_length=120,
        min_length=2,
        help_text="Nome completo do beneficiário"
    )
    
    beneficiary_cpf = serializers.CharField(
        max_length=14,
        help_text="CPF do beneficiário (apenas números ou com formatação)"
    )
    
    pix_key = serializers.CharField(
        max_length=77,
        help_text="Chave PIX (CPF, email, telefone ou chave aleatória)"
    )
    
    beneficiary_address = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Endereço do beneficiário (opcional)"
    )
    
    def validate_beneficiary_cpf(self, value):
        """Valida o CPF do beneficiário"""
        # Remove caracteres não numéricos
        cpf = re.sub(r'\D', '', value)
        
        if len(cpf) != 11:
            raise serializers.ValidationError("CPF deve ter 11 dígitos")
        
        # Verifica se não são todos os dígitos iguais
        if cpf == cpf[0] * 11:
            raise serializers.ValidationError("CPF inválido")
        
        # Validação completa do CPF
        transfer_service = TransferService()
        if not transfer_service._validate_cpf(cpf):
            raise serializers.ValidationError("CPF inválido")
        
        return cpf
    
    def validate_pix_key(self, value):
        """Valida a chave PIX"""
        transfer_service = TransferService()
        if not transfer_service._validate_pix_key(value):
            raise serializers.ValidationError("Chave PIX inválida")
        
        return value.strip()
    
    def validate_beneficiary_name(self, value):
        """Valida o nome do beneficiário"""
        name = value.strip()
        
        if not name:
            raise serializers.ValidationError("Nome é obrigatório")
        
        # Verifica se contém apenas letras, espaços e alguns caracteres especiais
        if not re.match(r"^[a-zA-ZÀ-ÿ\s'.-]+$", name):
            raise serializers.ValidationError("Nome contém caracteres inválidos")
        
        return name


class TransferCalculationSerializer(serializers.Serializer):
    """Serializer para cálculo de valores de transferência"""
    
    amount_usd = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2,
        min_value=Decimal('10.00'),
        max_value=Decimal('10000.00')
    )


class ExchangeRateSnapshotSerializer(serializers.ModelSerializer):
    """Serializer para snapshot de taxa de câmbio"""
    
    class Meta:
        model = ExchangeRateSnapshot
        fields = [
            'usd_to_brl_rate',
            'rate_source',
            'rate_timestamp',
            'spread_percentage',
            'final_rate'
        ]


class TransferStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer para histórico de status"""
    
    class Meta:
        model = TransferStatusHistory
        fields = [
            'previous_status',
            'new_status',
            'changed_by',
            'changed_at',
            'notes'
        ]


class TransferDetailSerializer(serializers.ModelSerializer):
    """Serializer detalhado para transferências"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    client_name = serializers.CharField(source='client.name', read_only=True)
    client_phone = serializers.CharField(source='client.phone', read_only=True)
    rate_snapshot = ExchangeRateSnapshotSerializer(read_only=True)
    status_history = TransferStatusHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Transfer
        fields = [
            'transfer_id',
            'status',
            'status_display',
            'client_name',
            'client_phone',
            'beneficiary_name',
            'beneficiary_cpf',
            'pix_key',
            'beneficiary_address',
            'amount_usd',
            'exchange_rate',
            'service_fee',
            'total_amount_usd',
            'amount_brl_estimated',
            'amount_brl_final',
            'payment_method',
            'payment_reference',
            'payment_link',
            'external_reference',
            'notes',
            'created_at',
            'updated_at',
            'payment_confirmed_at',
            'completed_at',
            'rate_snapshot',
            'status_history'
        ]
        read_only_fields = [
            'transfer_id',
            'exchange_rate',
            'service_fee',
            'total_amount_usd',
            'amount_brl_estimated',
            'created_at',
            'updated_at',
            'payment_confirmed_at',
            'completed_at'
        ]


class TransferListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para lista de transferências"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    client_name = serializers.CharField(source='client.name', read_only=True)
    
    class Meta:
        model = Transfer
        fields = [
            'transfer_id',
            'status',
            'status_display',
            'client_name',
            'beneficiary_name',
            'amount_usd',
            'total_amount_usd',
            'amount_brl_estimated',
            'created_at',
            'updated_at'
        ]


class TransferStatusUpdateSerializer(serializers.Serializer):
    """Serializer para atualização de status"""
    
    status = serializers.ChoiceField(
        choices=Transfer.STATUS_CHOICES,
        help_text="Novo status da transferência"
    )
    
    notes = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Observações sobre a mudança de status"
    )
    
    changed_by = serializers.CharField(
        max_length=100,
        required=False,
        default='api',
        help_text="Quem fez a alteração"
    )


class TransferSummarySerializer(serializers.Serializer):
    """Serializer para resumo de transferência"""
    
    transfer_id = serializers.CharField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    
    client = serializers.DictField()
    beneficiary = serializers.DictField()
    amounts = serializers.DictField()
    payment = serializers.DictField()
    timestamps = serializers.DictField()
    
    notes = serializers.CharField(allow_blank=True)
    external_reference = serializers.CharField(allow_blank=True)


class PaymentLinkSerializer(serializers.Serializer):
    """Serializer para link de pagamento"""
    
    payment_link = serializers.URLField(
        help_text="Link para pagamento da transferência"
    )
    
    transfer_id = serializers.CharField(
        help_text="ID da transferência"
    )
    
    total_amount_usd = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Valor total em USD"
    )
    
    expires_at = serializers.DateTimeField(
        required=False,
        help_text="Data de expiração do link (opcional)"
    )