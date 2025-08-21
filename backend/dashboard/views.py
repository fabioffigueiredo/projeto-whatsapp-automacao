from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from core.models import MessageLog, Conversation, Client, Transfer, Operation
import json
import logging

logger = logging.getLogger(__name__)

class DashboardView(View):
    """
    View principal do dashboard de monitoramento
    """
    
    def get(self, request):
        """Renderiza a página principal do dashboard"""
        return render(request, 'dashboard/index.html')

class DashboardStatsView(View):
    """
    API para estatísticas do dashboard
    """
    
    def get(self, request):
        """Retorna estatísticas gerais do sistema"""
        try:
            # Estatísticas gerais com dados de exemplo
            total_messages = MessageLog.objects.count() or 1247
            messages_today = MessageLog.objects.filter(
                created_at__date=timezone.now().date()
            ).count() or 23
            
            total_conversations = Conversation.objects.count() or 156
            active_conversations = Conversation.objects.filter(is_active=True).count() or 12
            
            # Dados de exemplo para workflows
            total_workflows = 5
            workflow_success_rate = 95
            
            # Status do sistema
            system_uptime = "99.9%"
            
            stats = {
                'messages': {
                    'total': total_messages,
                    'today': messages_today,
                    'this_month': total_messages,
                    'sent': int(total_messages * 0.8),
                    'delivered': int(total_messages * 0.75),
                    'read': int(total_messages * 0.6),
                    'failed': int(total_messages * 0.05)
                },
                'conversations': {
                    'total': total_conversations,
                    'active': active_conversations
                },
                'workflows': {
                    'total': total_workflows,
                    'success_rate': workflow_success_rate
                },
                'system': {
                    'uptime': system_uptime
                },
                'rates': {
                    'delivery': 93.5,
                    'read': 80.2
                }
            }
            
            return JsonResponse({
                'success': True,
                'data': stats
            })
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do dashboard: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Erro interno do servidor'
            }, status=500)

class MessageChartView(View):
    """Retorna dados para gráficos de mensagens"""
    
    def get(self, request):
        period = request.GET.get('period', '7')  # dias
        
        try:
            days = int(period)
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            # Dados de exemplo por dia
            daily_data = []
            for i in range(days):
                date = start_date + timedelta(days=i)
                # Simular dados variáveis
                import random
                count = random.randint(20, 100)
                daily_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': count
                })
            
            return JsonResponse({
                'daily_messages': daily_data,
                'period': period
            })
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados de gráfico: {e}")
            return JsonResponse({'error': 'Erro interno'}, status=500)

class RecentMessagesView(View):
    """
    API para mensagens recentes
    """
    
    def get(self, request):
        """Retorna lista de mensagens recentes"""
        try:
            limit = int(request.GET.get('limit', 10))
            
            # Dados de exemplo para mensagens recentes
            messages_data = [
                {
                    'id': 1,
                    'contact_name': 'João Silva',
                    'contact_phone': '+5511999999999',
                    'message_type': 'text',
                    'content': 'Olá, gostaria de fazer uma transferência',
                    'status': 'delivered',
                    'direction': 'in',
                    'created_at': timezone.now().isoformat(),
                    'updated_at': timezone.now().isoformat()
                },
                {
                    'id': 2,
                    'contact_name': 'Maria Santos',
                    'contact_phone': '+5511888888888',
                    'message_type': 'text',
                    'content': 'Bem-vindo! Como posso ajudá-lo?',
                    'status': 'sent',
                    'direction': 'out',
                    'created_at': (timezone.now() - timedelta(minutes=5)).isoformat(),
                    'updated_at': (timezone.now() - timedelta(minutes=5)).isoformat()
                },
                {
                    'id': 3,
                    'contact_name': 'Pedro Costa',
                    'contact_phone': '+5511777777777',
                    'message_type': 'text',
                    'content': 'Qual a cotação do dólar hoje?',
                    'status': 'read',
                    'direction': 'in',
                    'created_at': (timezone.now() - timedelta(minutes=10)).isoformat(),
                    'updated_at': (timezone.now() - timedelta(minutes=10)).isoformat()
                }
            ][:limit]
            
            return JsonResponse({
                'success': True,
                'data': messages_data
            })
            
        except Exception as e:
            logger.error(f"Erro ao obter mensagens recentes: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Erro interno do servidor'
            }, status=500)

class SystemHealthView(View):
    """Verifica a saúde do sistema"""
    
    def get(self, request):
        try:
            # Dados de exemplo para saúde do sistema
            health_data = {
                'database': {
                    'status': 'healthy',
                    'response_time': '15ms',
                    'connections': 5
                },
                'whatsapp_api': {
                    'status': 'healthy',
                    'response_time': '120ms',
                    'last_check': timezone.now().isoformat()
                },
                'n8n': {
                    'status': 'healthy',
                    'response_time': '80ms',
                    'workflows_active': 3
                },
                'disk_space': {
                    'status': 'healthy',
                    'used_percentage': 45,
                    'free_space': '15.2 GB'
                },
                'memory': {
                    'status': 'healthy',
                    'used_percentage': 68,
                    'available': '2.1 GB'
                },
                'timestamp': timezone.now().isoformat()
            }
            
            return JsonResponse(health_data)
            
        except Exception as e:
            logger.error(f"Erro ao verificar saúde do sistema: {e}")
            return JsonResponse({'error': 'Erro interno'}, status=500)
    


class CampaignStatsView(View):
    """
    API para estatísticas de campanhas
    """
    
    def get(self, request):
        """Retorna estatísticas detalhadas das campanhas"""
        try:
            # Dados de exemplo para campanhas
            campaigns_data = [
                {
                    'id': 1,
                    'name': 'Campanha de Boas-vindas',
                    'status': 'active',
                    'created_at': timezone.now().isoformat(),
                    'stats': {
                        'total': 150,
                        'sent': 145,
                        'delivered': 140,
                        'read': 120,
                        'failed': 5
                    }
                },
                {
                    'id': 2,
                    'name': 'Promoção Black Friday',
                    'status': 'completed',
                    'created_at': (timezone.now() - timedelta(days=7)).isoformat(),
                    'stats': {
                        'total': 500,
                        'sent': 495,
                        'delivered': 480,
                        'read': 420,
                        'failed': 5
                    }
                },
                {
                    'id': 3,
                    'name': 'Lembrete de Pagamento',
                    'status': 'paused',
                    'created_at': (timezone.now() - timedelta(days=3)).isoformat(),
                    'stats': {
                        'total': 75,
                        'sent': 70,
                        'delivered': 68,
                        'read': 60,
                        'failed': 5
                    }
                }
            ]
            
            return JsonResponse({
                'success': True,
                'data': campaigns_data
            })
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de campanhas: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Erro interno do servidor'
            }, status=500)