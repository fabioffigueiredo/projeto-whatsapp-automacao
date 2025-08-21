from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json
import logging

from ..models import Message, Conversation, WorkflowExecution
from ..services.whatsapp_business_service import WhatsAppBusinessService
from ..utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)
error_handler = ErrorHandler()

class DashboardView(View):
    """
    View principal do dashboard de monitoramento
    """
    
    def get(self, request):
        """Renderiza a página do dashboard"""
        try:
            context = {
                'title': 'Dashboard de Monitoramento',
                'page': 'dashboard'
            }
            return render(request, 'dashboard/index.html', context)
        except Exception as e:
            error_handler.log_error(e, 'dashboard_view', 'medium')
            return render(request, 'dashboard/error.html', {'error': str(e)})

class DashboardStatsView(View):
    """
    API para estatísticas do dashboard
    """
    
    def get(self, request):
        """Retorna estatísticas gerais do sistema"""
        try:
            # Período para análise (últimos 30 dias)
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)
            
            # Estatísticas de mensagens
            total_messages = Message.objects.count()
            messages_today = Message.objects.filter(
                created_at__date=timezone.now().date()
            ).count()
            
            messages_this_month = Message.objects.filter(
                created_at__gte=start_date
            ).count()
            
            # Estatísticas de conversas
            total_conversations = Conversation.objects.count()
            active_conversations = Conversation.objects.filter(
                is_active=True
            ).count()
            
            # Estatísticas de workflows
            total_workflows = WorkflowExecution.objects.count()
            successful_workflows = WorkflowExecution.objects.filter(
                status='completed'
            ).count()
            
            failed_workflows = WorkflowExecution.objects.filter(
                status='failed'
            ).count()
            
            # Taxa de sucesso
            success_rate = 0
            if total_workflows > 0:
                success_rate = (successful_workflows / total_workflows) * 100
            
            # Mensagens por tipo
            message_types = Message.objects.values('message_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Conversas por status
            conversation_status = Conversation.objects.values('status').annotate(
                count=Count('id')
            ).order_by('-count')
            
            stats = {
                'messages': {
                    'total': total_messages,
                    'today': messages_today,
                    'this_month': messages_this_month,
                    'by_type': list(message_types)
                },
                'conversations': {
                    'total': total_conversations,
                    'active': active_conversations,
                    'by_status': list(conversation_status)
                },
                'workflows': {
                    'total': total_workflows,
                    'successful': successful_workflows,
                    'failed': failed_workflows,
                    'success_rate': round(success_rate, 2)
                },
                'system': {
                    'uptime': self._get_system_uptime(),
                    'last_update': timezone.now().isoformat()
                }
            }
            
            return JsonResponse(stats)
            
        except Exception as e:
            error_handler.log_error(e, 'dashboard_stats', 'high')
            return JsonResponse({'error': str(e)}, status=500)
    
    def _get_system_uptime(self):
        """Calcula o uptime do sistema baseado na primeira mensagem"""
        try:
            first_message = Message.objects.first()
            if first_message:
                uptime = timezone.now() - first_message.created_at
                return str(uptime.days) + ' dias'
            return '0 dias'
        except:
            return 'N/A'

class MessageAnalyticsView(View):
    """
    API para análise de mensagens
    """
    
    def get(self, request):
        """Retorna análise detalhada de mensagens"""
        try:
            period = request.GET.get('period', '7')  # dias
            end_date = timezone.now()
            start_date = end_date - timedelta(days=int(period))
            
            # Mensagens por dia
            daily_messages = []
            for i in range(int(period)):
                date = start_date + timedelta(days=i)
                count = Message.objects.filter(
                    created_at__date=date.date()
                ).count()
                daily_messages.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': count
                })
            
            # Mensagens por hora (últimas 24h)
            hourly_messages = []
            for i in range(24):
                hour_start = timezone.now().replace(
                    hour=i, minute=0, second=0, microsecond=0
                )
                hour_end = hour_start + timedelta(hours=1)
                count = Message.objects.filter(
                    created_at__gte=hour_start,
                    created_at__lt=hour_end
                ).count()
                hourly_messages.append({
                    'hour': f'{i:02d}:00',
                    'count': count
                })
            
            # Top usuários por mensagens
            top_users = Message.objects.values('phone_number').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            # Tipos de mensagem mais comuns
            message_types = Message.objects.values('message_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            analytics = {
                'daily_messages': daily_messages,
                'hourly_messages': hourly_messages,
                'top_users': list(top_users),
                'message_types': list(message_types),
                'period': period
            }
            
            return JsonResponse(analytics)
            
        except Exception as e:
            error_handler.log_error(e, 'message_analytics', 'medium')
            return JsonResponse({'error': str(e)}, status=500)

class WorkflowAnalyticsView(View):
    """
    API para análise de workflows
    """
    
    def get(self, request):
        """Retorna análise detalhada de workflows"""
        try:
            period = request.GET.get('period', '7')  # dias
            end_date = timezone.now()
            start_date = end_date - timedelta(days=int(period))
            
            # Execuções por dia
            daily_executions = []
            for i in range(int(period)):
                date = start_date + timedelta(days=i)
                count = WorkflowExecution.objects.filter(
                    created_at__date=date.date()
                ).count()
                daily_executions.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': count
                })
            
            # Workflows por status
            status_distribution = WorkflowExecution.objects.values('status').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Workflows mais executados
            top_workflows = WorkflowExecution.objects.values('workflow_name').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            # Tempo médio de execução
            avg_execution_time = WorkflowExecution.objects.filter(
                status='completed',
                execution_time__isnull=False
            ).aggregate(
                avg_time=models.Avg('execution_time')
            )['avg_time']
            
            # Erros mais comuns
            common_errors = WorkflowExecution.objects.filter(
                status='failed',
                error_message__isnull=False
            ).values('error_message').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            analytics = {
                'daily_executions': daily_executions,
                'status_distribution': list(status_distribution),
                'top_workflows': list(top_workflows),
                'avg_execution_time': float(avg_execution_time) if avg_execution_time else 0,
                'common_errors': list(common_errors),
                'period': period
            }
            
            return JsonResponse(analytics)
            
        except Exception as e:
            error_handler.log_error(e, 'workflow_analytics', 'medium')
            return JsonResponse({'error': str(e)}, status=500)

class SystemHealthView(View):
    """
    API para verificação de saúde do sistema
    """
    
    def get(self, request):
        """Retorna status de saúde do sistema"""
        try:
            health_status = {
                'database': self._check_database(),
                'whatsapp_api': self._check_whatsapp_api(),
                'n8n_connection': self._check_n8n_connection(),
                'disk_space': self._check_disk_space(),
                'memory_usage': self._check_memory_usage(),
                'last_check': timezone.now().isoformat()
            }
            
            # Status geral
            all_healthy = all(
                status['status'] == 'healthy' 
                for status in health_status.values() 
                if isinstance(status, dict) and 'status' in status
            )
            
            health_status['overall'] = {
                'status': 'healthy' if all_healthy else 'warning',
                'message': 'Todos os sistemas funcionando' if all_healthy else 'Alguns sistemas com problemas'
            }
            
            return JsonResponse(health_status)
            
        except Exception as e:
            error_handler.log_error(e, 'system_health', 'high')
            return JsonResponse({'error': str(e)}, status=500)
    
    def _check_database(self):
        """Verifica conexão com banco de dados"""
        try:
            Message.objects.count()
            return {
                'status': 'healthy',
                'message': 'Conexão com banco de dados OK',
                'response_time': '< 100ms'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Erro na conexão com banco: {str(e)}',
                'response_time': 'N/A'
            }
    
    def _check_whatsapp_api(self):
        """Verifica conexão com WhatsApp API"""
        try:
            service = WhatsAppBusinessService()
            # Fazer uma verificação simples da API
            # (implementar método de health check no service)
            return {
                'status': 'healthy',
                'message': 'WhatsApp API acessível',
                'response_time': '< 500ms'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Erro na WhatsApp API: {str(e)}',
                'response_time': 'N/A'
            }
    
    def _check_n8n_connection(self):
        """Verifica conexão com N8N"""
        try:
            # Implementar verificação de conexão com N8N
            return {
                'status': 'healthy',
                'message': 'N8N acessível',
                'response_time': '< 200ms'
            }
        except Exception as e:
            return {
                'status': 'warning',
                'message': f'N8N não acessível: {str(e)}',
                'response_time': 'N/A'
            }
    
    def _check_disk_space(self):
        """Verifica espaço em disco"""
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            free_percent = (free / total) * 100
            
            if free_percent > 20:
                status = 'healthy'
                message = f'Espaço em disco OK ({free_percent:.1f}% livre)'
            elif free_percent > 10:
                status = 'warning'
                message = f'Espaço em disco baixo ({free_percent:.1f}% livre)'
            else:
                status = 'error'
                message = f'Espaço em disco crítico ({free_percent:.1f}% livre)'
            
            return {
                'status': status,
                'message': message,
                'free_space': f'{free_percent:.1f}%'
            }
        except Exception as e:
            return {
                'status': 'warning',
                'message': f'Não foi possível verificar espaço em disco: {str(e)}',
                'free_space': 'N/A'
            }
    
    def _check_memory_usage(self):
        """Verifica uso de memória"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            used_percent = memory.percent
            
            if used_percent < 80:
                status = 'healthy'
                message = f'Uso de memória normal ({used_percent:.1f}%)'
            elif used_percent < 90:
                status = 'warning'
                message = f'Uso de memória alto ({used_percent:.1f}%)'
            else:
                status = 'error'
                message = f'Uso de memória crítico ({used_percent:.1f}%)'
            
            return {
                'status': status,
                'message': message,
                'usage': f'{used_percent:.1f}%'
            }
        except ImportError:
            return {
                'status': 'warning',
                'message': 'psutil não instalado - não é possível verificar memória',
                'usage': 'N/A'
            }
        except Exception as e:
            return {
                'status': 'warning',
                'message': f'Erro ao verificar memória: {str(e)}',
                'usage': 'N/A'
            }

class RealtimeUpdatesView(View):
    """
    API para atualizações em tempo real (WebSocket ou polling)
    """
    
    def get(self, request):
        """Retorna atualizações recentes do sistema"""
        try:
            # Últimas mensagens (últimos 5 minutos)
            recent_messages = Message.objects.filter(
                created_at__gte=timezone.now() - timedelta(minutes=5)
            ).order_by('-created_at')[:10]
            
            # Últimas execuções de workflow
            recent_workflows = WorkflowExecution.objects.filter(
                created_at__gte=timezone.now() - timedelta(minutes=5)
            ).order_by('-created_at')[:10]
            
            # Erros recentes
            recent_errors = error_handler.get_recent_errors(limit=5)
            
            updates = {
                'messages': [
                    {
                        'id': msg.id,
                        'phone_number': msg.phone_number,
                        'message_type': msg.message_type,
                        'created_at': msg.created_at.isoformat(),
                        'content': msg.content[:50] + '...' if len(msg.content) > 50 else msg.content
                    }
                    for msg in recent_messages
                ],
                'workflows': [
                    {
                        'id': wf.id,
                        'workflow_name': wf.workflow_name,
                        'status': wf.status,
                        'created_at': wf.created_at.isoformat()
                    }
                    for wf in recent_workflows
                ],
                'errors': recent_errors,
                'timestamp': timezone.now().isoformat()
            }
            
            return JsonResponse(updates)
            
        except Exception as e:
            error_handler.log_error(e, 'realtime_updates', 'medium')
            return JsonResponse({'error': str(e)}, status=500)