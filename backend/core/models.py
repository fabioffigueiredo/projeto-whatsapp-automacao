from django.db import models
from django.utils import timezone

class ProviderConfig(models.Model):
    TYPE_CHOICES = [("whatsapp","WhatsApp"),("payments","Payments"),("xps247","XPS247"),("fx","FX")]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    name = models.CharField(max_length=50)
    base_url = models.URLField(blank=True, null=True)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    secret = models.CharField(max_length=255, blank=True, null=True)
    active = models.BooleanField(default=True)
    def __str__(self): return f"{self.type}:{self.name}"

class MessageTemplate(models.Model):
    code = models.CharField(max_length=60, unique=True)
    text = models.TextField()
    locale = models.CharField(max_length=10, default="pt-BR")
    def __str__(self): return self.code

class Conversation(models.Model):
    external_user_id = models.CharField(max_length=50)  # telefone
    state_node = models.CharField(max_length=60, default="START")
    context_data = models.JSONField(default=dict, blank=True)  # dados temporários da conversa
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Conversation {self.external_user_id} - {self.state_node}"

class MessageLog(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    direction = models.CharField(max_length=3, choices=[("in","in"),("out","out")])
    payload = models.JSONField()
    status = models.CharField(max_length=30, default="ok")
    created_at = models.DateTimeField(auto_now_add=True)

class WebhookLog(models.Model):
    source = models.CharField(max_length=20)
    payload = models.JSONField()
    status = models.CharField(max_length=30, default="ok")
    received_at = models.DateTimeField(auto_now_add=True)

class Client(models.Model):
    external_id = models.CharField(max_length=60, blank=True, null=True)  # id XPS247
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30, unique=True)
    email = models.EmailField(blank=True, null=True)
    username = models.CharField(max_length=50, blank=True, null=True)
    password_hash = models.CharField(max_length=255, blank=True, null=True)
    is_registered = models.BooleanField(default=False)
    registration_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.phone})"

class Operation(models.Model):
    STATUS = [("draft","draft"),("awaiting_payment","awaiting_payment"),("paid","paid"),("failed","failed"),("cancelled","cancelled")]
    client = models.ForeignKey(Client, on_delete=models.PROTECT)
    beneficiary_name = models.CharField(max_length=120, blank=True, default="")
    beneficiary_cpf = models.CharField(max_length=20, blank=True, default="")
    pix_key = models.CharField(max_length=120, blank=True, default="")
    address = models.TextField(blank=True, default="")
    amount_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rate_used = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    fees = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_brl_estimated = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default="draft")
    payment_link = models.URLField(blank=True, null=True)
    payment_provider_ref = models.CharField(max_length=120, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Transfer(models.Model):
    """Modelo principal para transferências de dinheiro"""
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('pending_payment', 'Aguardando Pagamento'),
        ('payment_confirmed', 'Pagamento Confirmado'),
        ('processing', 'Processando'),
        ('completed', 'Concluída'),
        ('failed', 'Falhou'),
        ('cancelled', 'Cancelada'),
    ]
    
    # Identificação
    transfer_id = models.CharField(max_length=20, unique=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='transfers')
    
    # Dados do beneficiário
    beneficiary_name = models.CharField(max_length=120)
    beneficiary_cpf = models.CharField(max_length=14)
    pix_key = models.CharField(max_length=120)
    beneficiary_address = models.TextField(blank=True)
    
    # Valores e taxas
    amount_usd = models.DecimalField(max_digits=12, decimal_places=2)
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=6)
    service_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount_usd = models.DecimalField(max_digits=12, decimal_places=2)  # amount_usd + service_fee
    amount_brl_estimated = models.DecimalField(max_digits=12, decimal_places=2)
    amount_brl_final = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Status e controle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    payment_method = models.CharField(max_length=50, blank=True)  # 'stripe', 'paypal', etc.
    payment_reference = models.CharField(max_length=120, blank=True)
    payment_link = models.URLField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadados
    notes = models.TextField(blank=True)
    external_reference = models.CharField(max_length=120, blank=True)  # Referência do provedor externo
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['transfer_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Transfer {self.transfer_id} - {self.client.name} - ${self.amount_usd}"
    
    def save(self, *args, **kwargs):
        if not self.transfer_id:
            # Gerar ID único para a transferência
            import uuid
            self.transfer_id = f"TRF{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

class TransferStatusHistory(models.Model):
    """Histórico de mudanças de status das transferências"""
    transfer = models.ForeignKey(Transfer, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.CharField(max_length=50, default='system')  # 'system', 'user', 'webhook'
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transfer.transfer_id}: {self.previous_status} → {self.new_status}"

class ExchangeRateSnapshot(models.Model):
    """Snapshot das taxas de câmbio no momento da transferência"""
    transfer = models.OneToOneField(Transfer, on_delete=models.CASCADE, related_name='rate_snapshot')
    usd_to_brl_rate = models.DecimalField(max_digits=12, decimal_places=6)
    rate_source = models.CharField(max_length=50)  # 'fixer.io', 'exchangerate-api', etc.
    rate_timestamp = models.DateTimeField()
    spread_percentage = models.DecimalField(max_digits=5, decimal_places=4, default=0)  # Spread aplicado
    final_rate = models.DecimalField(max_digits=12, decimal_places=6)  # Taxa final com spread
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Rate for {self.transfer.transfer_id}: {self.final_rate}"
