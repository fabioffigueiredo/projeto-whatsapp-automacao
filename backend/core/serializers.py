from rest_framework import serializers
class WebhookIn(serializers.Serializer):
    phone = serializers.CharField()
    message = serializers.CharField()

class PaymentWebhookIn(serializers.Serializer):
    ref = serializers.CharField()
    status = serializers.CharField()
