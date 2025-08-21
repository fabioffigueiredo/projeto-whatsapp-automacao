from django.urls import path, include
from ..views import whatsapp_webhook, payment_webhook, client_login, client_register, complete_registration, client_profile, change_password
from ..views import conversation_api

urlpatterns = [
    path('webhook/', whatsapp_webhook, name='whatsapp_webhook'),
    path('payment-webhook/', payment_webhook, name='payment_webhook'),
    
    # Authentication endpoints
    path('auth/login/', client_login, name='client_login'),
    path('auth/register/', client_register, name='client_register'),
    path('auth/complete/', complete_registration, name='complete_registration'),
    path('auth/profile/', client_profile, name='client_profile'),
    path('auth/change-password/', change_password, name='change_password'),
    
    # Conversation API
    path('conversation/last-response/<str:phone_number>/', conversation_api.get_last_response, name='last_response'),
    
    # Transfer endpoints
    path('transfers/', include('core.urls.transfer_urls')),
]