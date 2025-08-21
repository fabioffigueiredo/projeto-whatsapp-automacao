from django.urls import path, include
from ..views import whatsapp_webhook, payment_webhook, conversation_api
# Temporarily commented out auth views due to JWT dependency
# from ..views import client_login, client_register, complete_registration, client_profile, change_password
# from ..views.n8n_integration import n8n_analytics, n8n_notifications, n8n_payments, n8n_webhook  # Comentado - módulo não existe

urlpatterns = [
    path('webhook/', whatsapp_webhook, name='whatsapp_webhook'),
    path('payment-webhook/', payment_webhook, name='payment_webhook'),
    
    # Authentication endpoints (temporarily commented due to JWT dependency)
    # path('auth/login/', client_login, name='client_login'),
    # path('auth/register/', client_register, name='client_register'),
    # path('auth/complete/', complete_registration, name='complete_registration'),
    # path('auth/profile/', client_profile, name='client_profile'),
    # path('auth/change-password/', change_password, name='change_password'),
    
    # Conversation API
    path('conversation/last-response/<str:phone_number>/', conversation_api.get_last_response, name='last_response'),
    
    # Transfer endpoints
    path('transfers/', include('core.urls.transfer_urls')),
    
    # N8n integration endpoints - Comentado temporariamente
    # path('n8n/analytics/', n8n_analytics, name='n8n_analytics'),
    # path('n8n/notifications/', n8n_notifications, name='n8n_notifications'),
    # path('n8n/payments/', n8n_payments, name='n8n_payments'),
    # path('n8n/webhook/', n8n_webhook, name='n8n_webhook'),
]