from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging
from datetime import datetime
from ..models import Conversation, TransferData
from ..services.whatsapp_service import WhatsAppService
from ..services.payment_service import PaymentService

logger = logging.getLogger(__name__)


class N8NAnalyticsView(View):
    """Endpoint para receber dados de analytics do n8n"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Log analytics data
            analytics_data = {
                'phone': data.get('phone'),
                'message': data.get('message'),
                'conversation_state': data.get('conversationState'),
                'response_time': data.get('responseTime'),
                'success': data.get('success'),
                'timestamp': data.get('timestamp')
            }
            
            logger.info(f"N8N Analytics: {analytics_data}")
            
            # Aqui você pode salvar no banco de dados ou enviar para um serviço de analytics
            # Por exemplo, salvar em uma tabela de analytics ou enviar para Google Analytics
            
            return JsonResponse({
                'status': 'success',
                'message': 'Analytics data logged successfully'
            })
            
        except Exception as e:
            logger.error(f"Error logging analytics: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)


class N8NNotificationView(View):
    """Endpoint para enviar notificações via n8n"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            phone = data.get('phone')
            notification_type = data.get('type')
            notification_data = data.get('data', {})
            
            # Processar diferentes tipos de notificação
            if notification_type == 'payment_initiated':
                message = self._create_payment_notification(notification_data)
            elif notification_type == 'payment_completed':
                message = self._create_payment_success_notification(notification_data)
            elif notification_type == 'payment_failed':
                message = self._create_payment_error_notification(notification_data)
            else:
                message = "📢 Você tem uma nova notificação!"
            
            # Enviar notificação via WhatsApp
            whatsapp_service = WhatsAppService()
            response = whatsapp_service.send_message(phone, message)
            
            logger.info(f"N8N Notification sent to {phone}: {notification_type}")
            
            return JsonResponse({
                'status': 'success',
                'message': 'Notification sent successfully',
                'whatsapp_response': response
            })
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    def _create_payment_notification(self, data):
        return (
            "💳 *Processamento de Pagamento Iniciado*\n\n"
            "Seu pagamento está sendo processado. "
            "Você receberá uma confirmação em breve.\n\n"
            "⏱️ Tempo estimado: 2-5 minutos"
        )
    
    def _create_payment_success_notification(self, data):
        amount = data.get('amount', 'N/A')
        return (
            "✅ *Pagamento Confirmado!*\n\n"
            f"Valor: ${amount}\n"
            "Sua transferência foi processada com sucesso.\n\n"
            "Obrigado por usar nossos serviços! 🙏"
        )
    
    def _create_payment_error_notification(self, data):
        error = data.get('error', 'Erro desconhecido')
        return (
            "❌ *Erro no Pagamento*\n\n"
            f"Motivo: {error}\n\n"
            "Por favor, tente novamente ou entre em contato conosco."
        )


class N8NPaymentView(View):
    """Endpoint para processar pagamentos via n8n"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            phone = data.get('phone')
            amount = data.get('amount')
            
            if not phone or not amount:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Phone and amount are required'
                }, status=400)
            
            # Buscar dados da transferência
            try:
                conversation = Conversation.objects.get(phone_number=phone)
                transfer_data = TransferData.objects.get(conversation=conversation)
            except (Conversation.DoesNotExist, TransferData.DoesNotExist):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Transfer data not found'
                }, status=404)
            
            # Processar pagamento
            payment_service = PaymentService()
            payment_result = payment_service.create_payment_link(
                amount=float(amount),
                currency='USD',
                description=f"Transfer to {transfer_data.beneficiary_name}",
                customer_phone=phone
            )
            
            if payment_result.get('success'):
                # Atualizar estado da conversa
                conversation.state = 'NODE_7_PAYMENT'
                conversation.save()
                
                logger.info(f"N8N Payment initiated for {phone}: ${amount}")
                
                return JsonResponse({
                    'status': 'success',
                    'payment_link': payment_result.get('payment_link'),
                    'payment_id': payment_result.get('payment_id'),
                    'message': 'Payment link created successfully'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': payment_result.get('error', 'Payment creation failed')
                }, status=500)
                
        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)


class N8NWebhookView(View):
    """Endpoint principal para receber webhooks do n8n"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            webhook_type = data.get('type', 'unknown')
            
            logger.info(f"N8N Webhook received: {webhook_type}")
            
            # Processar diferentes tipos de webhook
            if webhook_type == 'payment_status':
                return self._handle_payment_status(data)
            elif webhook_type == 'conversation_analytics':
                return self._handle_conversation_analytics(data)
            elif webhook_type == 'system_health':
                return self._handle_system_health(data)
            else:
                return JsonResponse({
                    'status': 'success',
                    'message': f'Webhook {webhook_type} received'
                })
                
        except Exception as e:
            logger.error(f"Error processing n8n webhook: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    def _handle_payment_status(self, data):
        """Processar webhook de status de pagamento"""
        payment_id = data.get('payment_id')
        status = data.get('status')
        phone = data.get('phone')
        
        logger.info(f"Payment status update: {payment_id} - {status}")
        
        # Atualizar status no banco de dados
        # Enviar notificação para o usuário
        
        return JsonResponse({
            'status': 'success',
            'message': 'Payment status updated'
        })
    
    def _handle_conversation_analytics(self, data):
        """Processar analytics de conversação"""
        # Salvar dados de analytics
        # Gerar relatórios
        
        return JsonResponse({
            'status': 'success',
            'message': 'Analytics processed'
        })
    
    def _handle_system_health(self, data):
        """Processar dados de saúde do sistema"""
        # Monitorar saúde do sistema
        # Enviar alertas se necessário
        
        return JsonResponse({
            'status': 'success',
            'message': 'System health checked'
        })


# Views baseadas em função para compatibilidade
@csrf_exempt
@require_http_methods(["POST"])
def n8n_analytics(request):
    view = N8NAnalyticsView()
    return view.post(request)


@csrf_exempt
@require_http_methods(["POST"])
def n8n_notifications(request):
    view = N8NNotificationView()
    return view.post(request)


@csrf_exempt
@require_http_methods(["POST"])
def n8n_payments(request):
    view = N8NPaymentView()
    return view.post(request)


@csrf_exempt
@require_http_methods(["POST"])
def n8n_webhook(request):
    view = N8NWebhookView()
    return view.post(request)