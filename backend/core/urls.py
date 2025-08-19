from django.urls import path
from .views import whatsapp_webhook, payment_webhook

urlpatterns = [
    path('webhook/whatsapp', whatsapp_webhook),
    path('webhook/payment', payment_webhook),
]
