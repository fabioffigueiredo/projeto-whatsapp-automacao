from django.db import models
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
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)
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
