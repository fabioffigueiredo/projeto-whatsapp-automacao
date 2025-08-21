from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
import logging

from ..serializers import WebhookIn, PaymentWebhookIn
from ..models import Conversation, MessageLog, Client, Operation, WebhookLog, Transfer
from ..services.fx import dolar_comercial
from ..services.payments import create_payment_link, verify_webhook_signature
from ..services.xps247 import find_client_by_phone
from ..services.whatsapp import whatsapp_service
from ..services.whatsapp_business_service import whatsapp_service as whatsapp_business_service
from ..services.conversation_handler import ConversationHandler
from decimal import Decimal

logger = logging.getLogger(__name__)

@api_view(["GET", "POST"])
@permission_classes([AllowAny])
@csrf_exempt
def whatsapp_webhook(request):
    """
    Webhook para receber mensagens do WhatsApp Business API
    GET: Verificação do webhook
    POST: Recebimento de mensagens
    """
    # Verificação do webhook (GET)
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")
        
        verified_challenge = whatsapp_business_service.verify_webhook(mode, token, challenge)
        if verified_challenge:
            return HttpResponse(verified_challenge, content_type="text/plain")
        else:
            return HttpResponse("Forbidden", status=403)
    
    # Processamento de mensagens (POST)
    try:
        # Validação de assinatura
        if hasattr(settings, 'WHATSAPP_APP_SECRET') and settings.WHATSAPP_APP_SECRET:
            signature = request.META.get('HTTP_X_HUB_SIGNATURE_256', '')
            payload = request.body.decode('utf-8')
            
            if not whatsapp_business_service.validate_webhook_signature(payload, signature):
                logger.warning("Invalid WhatsApp webhook signature")
                return HttpResponse("Forbidden", status=403)
        
        # Log do webhook recebido
        WebhookLog.objects.create(
            source="whatsapp",
            payload=request.data,
            status="received"
        )
        
        # Parse da mensagem do WhatsApp
        message_data = whatsapp_service.parse_webhook_message(request.data)
        if not message_data:
            logger.warning("No valid message found in WhatsApp webhook")
            return Response({"status": "no_message"}, status=200)
        
        phone = message_data["phone"]
        message_text = message_data["message"]
        message_id = message_data.get("message_id")
        
        # Marca mensagem como lida
        if message_id:
            try:
                whatsapp_business_service.mark_message_as_read(message_id)
            except Exception as e:
                logger.warning(f"Failed to mark message as read: {e}")
        
        # Processa a conversa usando o ConversationHandler
        conversation_handler = ConversationHandler()
        reply = conversation_handler.process_message(phone, message_text)
        
        # Envia resposta via WhatsApp Business API
        if reply:
            try:
                send_result = whatsapp_business_service.send_text_message(phone, reply)
                logger.info(f"WhatsApp response sent to {phone}: {send_result}")
            except Exception as e:
                logger.error(f"Failed to send WhatsApp message to {phone}: {e}")
                # Fallback para o serviço antigo se necessário
                try:
                    send_result = whatsapp_service.send_message(phone, reply)
                    logger.info(f"WhatsApp response sent via fallback to {phone}: {send_result}")
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed for {phone}: {fallback_error}")
        
        return Response({"status": "success"}, status=200)
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}")
        WebhookLog.objects.create(
            source="whatsapp",
            payload=request.data,
            status="error"
        )
        return Response({"error": "Internal error"}, status=500)



@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def payment_webhook(request):
    """
    Webhook para receber notificações de pagamento
    """
    try:
        # Log do webhook recebido
        WebhookLog.objects.create(
            source="payment",
            payload=request.data,
            status="received"
        )
        
        # Verificar assinatura do webhook
        if not verify_webhook_signature(request):
            logger.warning("Invalid webhook signature for payment")
            return Response({"ok": False, "error": "invalid signature"}, status=403)

        ser = PaymentWebhookIn(data=request.data)
        ser.is_valid(raise_exception=True)
        ref = ser.validated_data["ref"]
        status_in = ser.validated_data["status"]

        # Buscar transferência pela referência de pagamento
        transfer = Transfer.objects.filter(payment_reference=ref).first()
        if not transfer:
            logger.error(f"Transfer not found for payment ref: {ref}")
            return Response({"ok": False, "error": "transfer not found"}, status=404)

        # Atualizar status da transferência usando TransferService
        from ..services.transfer_service import TransferService
        transfer_service = TransferService()
        old_status = transfer.status
        
        if status_in == "paid":
            transfer_service.update_transfer_status(transfer, "payment_confirmed", "webhook", "Pagamento confirmado via webhook")
        else:
            transfer_service.update_transfer_status(transfer, "failed", "webhook", "Pagamento falhou via webhook")
        
        logger.info(f"Transfer {transfer.id} status updated from {old_status} to {status_in}")
        
        # Notificar cliente via WhatsApp usando ConversationHandler
        conversation_handler = ConversationHandler()
        notification_sent = conversation_handler.handle_payment_confirmation(transfer.id, status_in)
        
        if notification_sent:
            logger.info(f"Payment confirmation sent to {transfer.client.phone}")
        else:
            logger.warning(f"Failed to send payment confirmation for transfer {transfer.id}")
        
        return Response({"ok": True})
        
    except Exception as e:
        logger.error(f"Error processing payment webhook: {e}")
        WebhookLog.objects.create(
            source="payment",
            payload=request.data,
            status="error"
        )
        return Response({"error": "Internal error"}, status=500)
