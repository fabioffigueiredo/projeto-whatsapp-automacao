from rest_framework import serializers
from ..models import WebhookLog, Operation, Client

class WebhookIn(serializers.Serializer):
    phone = serializers.CharField(max_length=30)
    message = serializers.CharField(max_length=1000)

class PaymentWebhookIn(serializers.Serializer):
    ref = serializers.CharField(max_length=120)
    status = serializers.CharField(max_length=30)