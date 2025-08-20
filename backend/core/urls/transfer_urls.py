from django.urls import path
from ..views.transfer_views import (
    calculate_transfer,
    create_transfer,
    get_transfer,
    list_transfers,
    update_transfer_status,
    get_transfer_summary,
    generate_payment_link,
    check_payment_status,
    admin_update_transfer_status
)

app_name = 'transfers'

urlpatterns = [
    # Endpoints para clientes
    path('calculate/', calculate_transfer, name='calculate'),
    path('create/', create_transfer, name='create'),
    path('list/', list_transfers, name='list'),
    path('<str:transfer_id>/', get_transfer, name='detail'),
    path('<str:transfer_id>/summary/', get_transfer_summary, name='summary'),
    path('<str:transfer_id>/status/', update_transfer_status, name='update_status'),
    path('<str:transfer_id>/payment-link/', generate_payment_link, name='payment_link'),
    path('<str:transfer_id>/payment-status/', check_payment_status, name='check_payment_status'),
    
    # Endpoints administrativos
    path('admin/<str:transfer_id>/status/', admin_update_transfer_status, name='admin_update_status'),
]