from typing import Dict, List, Any, Optional, Tuple
from django.conf import settings
from django.utils import timezone
import logging
import re
from datetime import datetime, timedelta

from .message_templates import MessageTemplates
from .whatsapp_business_service import WhatsAppBusinessService
from ..models import Conversation, Client, MessageLog

logger = logging.getLogger(__name__)

class AutoMessageHandler:
    """
    Sistema avançado de mensagens automáticas com:
    - Respostas baseadas em palavras-chave
    - Templates personalizados
    - Contexto de conversa
    - Análise de sentimento básica
    - Horário de funcionamento
    """
    
    def __init__(self):
        self.templates = MessageTemplates()
        self.whatsapp_service = WhatsAppBusinessService()
        
        # Palavras-chave e suas respostas
        self.keyword_responses = {
            # Saudações
            'ola|oi|olá|bom dia|boa tarde|boa noite|hey|hello': {
                'response': 'welcome',
                'priority': 1
            },
            
            # Menu e navegação
            'menu|opcoes|opções|ajuda|help': {
                'response': 'menu',
                'priority': 1
            },
            
            # Cotação e câmbio
            'cotacao|cotação|dolar|dólar|cambio|câmbio|taxa|rate': {
                'response': 'exchange_rate',
                'priority': 2
            },
            
            # Transferência
            'transferencia|transferência|enviar|mandar|remessa|transfer': {
                'response': 'transfer_info',
                'priority': 2
            },
            
            # Suporte
            'suporte|atendente|humano|pessoa|falar|conversar|problema': {
                'response': 'human_support',
                'priority': 3
            },
            
            # Status e consulta
            'status|consultar|verificar|operacao|operação|pedido': {
                'response': 'operation_status',
                'priority': 2
            },
            
            # Informações da empresa
            'sobre|empresa|quem|informacao|informação|contato': {
                'response': 'company_info',
                'priority': 2
            },
            
            # Despedidas
            'tchau|bye|obrigado|obrigada|valeu|até|adeus': {
                'response': 'goodbye',
                'priority': 1
            },
            
            # Emergência/Urgência
            'urgente|emergencia|emergência|rapido|rápido|agora': {
                'response': 'urgent_support',
                'priority': 4
            }
        }
        
        # Horário de funcionamento
        self.business_hours = {
            'monday': {'start': '09:00', 'end': '18:00'},
            'tuesday': {'start': '09:00', 'end': '18:00'},
            'wednesday': {'start': '09:00', 'end': '18:00'},
            'thursday': {'start': '09:00', 'end': '18:00'},
            'friday': {'start': '09:00', 'end': '18:00'},
            'saturday': {'start': '09:00', 'end': '12:00'},
            'sunday': None  # Fechado
        }
    
    def process_auto_message(self, phone: str, message: str, conversation: Optional[Conversation] = None) -> str:
        """
        Processa mensagem e retorna resposta automática apropriada
        
        Args:
            phone: Número do telefone
            message: Mensagem recebida
            conversation: Conversa existente (opcional)
            
        Returns:
            Resposta automática ou None se não houver resposta
        """
        try:
            # Normaliza a mensagem
            normalized_message = self._normalize_message(message)
            
            # Verifica se é primeira interação
            if not conversation or not conversation.context_data:
                return self._handle_first_interaction(phone, normalized_message)
            
            # Verifica palavras-chave
            keyword_response = self._check_keywords(normalized_message)
            if keyword_response:
                return self._generate_response(keyword_response, phone, conversation)
            
            # Verifica contexto da conversa
            context_response = self._check_conversation_context(conversation, normalized_message)
            if context_response:
                return context_response
            
            # Resposta padrão para mensagens não reconhecidas
            return self._generate_default_response(conversation)
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem automática de {phone}: {e}")
            return self.templates.error_message("general")
    
    def _normalize_message(self, message: str) -> str:
        """
        Normaliza mensagem removendo acentos, caracteres especiais e convertendo para minúsculas
        """
        # Remove acentos e caracteres especiais
        normalized = message.lower().strip()
        
        # Remove emojis e caracteres especiais
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Remove espaços extras
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def _handle_first_interaction(self, phone: str, message: str) -> str:
        """
        Lida com primeira interação do usuário
        """
        # Verifica se é horário comercial
        if not self._is_business_hours():
            return self._get_after_hours_message()
        
        # Verifica se cliente já existe
        try:
            client = Client.objects.get(phone=phone)
            return self.templates.welcome_message(client.name)
        except Client.DoesNotExist:
            return self.templates.welcome_message()
    
    def _check_keywords(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Verifica se a mensagem contém palavras-chave conhecidas
        """
        best_match = None
        highest_priority = 0
        
        for pattern, response_config in self.keyword_responses.items():
            if re.search(pattern, message, re.IGNORECASE):
                if response_config['priority'] > highest_priority:
                    highest_priority = response_config['priority']
                    best_match = response_config
        
        return best_match
    
    def _generate_response(self, response_config: Dict[str, Any], phone: str, conversation: Optional[Conversation]) -> str:
        """
        Gera resposta baseada na configuração
        """
        response_type = response_config['response']
        
        response_map = {
            'welcome': self._get_welcome_response(phone),
            'menu': self.templates.menu_options(),
            'exchange_rate': self._get_exchange_rate_response(),
            'transfer_info': self.templates.transfer_instructions(),
            'human_support': self._get_support_response(),
            'operation_status': self._get_status_response(conversation),
            'company_info': self.templates.company_info(),
            'goodbye': self._get_goodbye_response(),
            'urgent_support': self._get_urgent_support_response()
        }
        
        return response_map.get(response_type, self.templates.error_message("invalid_option"))
    
    def _check_conversation_context(self, conversation: Conversation, message: str) -> Optional[str]:
        """
        Verifica contexto da conversa para respostas contextuais
        """
        context = conversation.context_data or {}
        
        # Se usuário está em processo de transferência
        if context.get('in_transfer_process'):
            return self._handle_transfer_context(conversation, message)
        
        # Se usuário está consultando cotação
        if context.get('checking_rates'):
            return self._handle_rate_context(conversation, message)
        
        # Se usuário está aguardando suporte
        if context.get('waiting_support'):
            return self._handle_support_context(conversation, message)
        
        return None
    
    def _handle_transfer_context(self, conversation: Conversation, message: str) -> str:
        """
        Lida com contexto de transferência
        """
        if re.search(r'cancelar|parar|sair', message, re.IGNORECASE):
            # Usuário quer cancelar
            conversation.context_data = {}
            conversation.save()
            return "❌ Processo de transferência cancelado.\n\nDigite *menu* para ver outras opções."
        
        return "📋 Você está em processo de transferência.\n\nPara cancelar, digite *cancelar*.\nPara continuar, siga as instruções anteriores."
    
    def _handle_rate_context(self, conversation: Conversation, message: str) -> str:
        """
        Lida com contexto de cotação
        """
        # Verifica se é uma moeda válida
        currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY']
        message_upper = message.upper()
        
        for currency in currencies:
            if currency in message_upper:
                return self._get_specific_rate(currency)
        
        return "💱 Moedas disponíveis: USD, EUR, GBP, CAD, AUD, JPY\n\nDigite o código da moeda para ver a cotação."
    
    def _handle_support_context(self, conversation: Conversation, message: str) -> str:
        """
        Lida com contexto de suporte
        """
        return "👨‍💼 Sua solicitação de suporte foi registrada.\n\nUm atendente entrará em contato em breve.\n\nEnquanto isso, posso ajudá-lo com informações básicas. Digite *menu* para ver as opções."
    
    def _get_welcome_response(self, phone: str) -> str:
        """
        Gera resposta de boas-vindas personalizada
        """
        try:
            client = Client.objects.get(phone=phone)
            return self.templates.welcome_message(client.name)
        except Client.DoesNotExist:
            return self.templates.welcome_message()
    
    def _get_exchange_rate_response(self) -> str:
        """
        Gera resposta com cotação atual
        """
        try:
            # Aqui você integraria com sua API de cotação
            # Por enquanto, valor simulado
            rate = 5.25  # Valor simulado
            return self.templates.exchange_rate_info("USD", rate)
        except Exception as e:
            logger.error(f"Erro ao buscar cotação: {e}")
            return "💱 Cotação temporariamente indisponível.\n\nTente novamente em alguns instantes ou fale com nosso suporte."
    
    def _get_support_response(self) -> str:
        """
        Gera resposta de suporte baseada no horário
        """
        if self._is_business_hours():
            return self.templates.human_support()
        else:
            return self._get_after_hours_message() + "\n\n" + self.templates.human_support()
    
    def _get_status_response(self, conversation: Optional[Conversation]) -> str:
        """
        Gera resposta de status de operação
        """
        if conversation and conversation.context_data.get('operation_id'):
            op_id = conversation.context_data['operation_id']
            return f"📊 Para consultar o status da operação {op_id}, entre em contato com nosso suporte.\n\n{self.templates.human_support()}"
        else:
            return "📊 Para consultar status de operação, preciso do ID da operação.\n\nEntre em contato com nosso suporte para mais informações."
    
    def _get_goodbye_response(self) -> str:
        """
        Gera resposta de despedida
        """
        return "👋 Obrigado por usar nossos serviços!\n\nSempre que precisar, estarei aqui para ajudar.\n\nTenha um ótimo dia! 😊"
    
    def _get_urgent_support_response(self) -> str:
        """
        Gera resposta para casos urgentes
        """
        return "🚨 **ATENDIMENTO URGENTE**\n\nSua solicitação foi marcada como urgente.\n\n📞 **Contato imediato:**\nTelefone: (11) 1234-5678\nWhatsApp: (11) 9 8765-4321\n\nUm especialista entrará em contato o mais rápido possível."
    
    def _get_specific_rate(self, currency: str) -> str:
        """
        Gera resposta com cotação específica de uma moeda
        """
        # Valores simulados - integrar com API real
        rates = {
            'USD': 5.25,
            'EUR': 5.85,
            'GBP': 6.45,
            'CAD': 3.95,
            'AUD': 3.55,
            'JPY': 0.038
        }
        
        rate = rates.get(currency, 0)
        if rate:
            return self.templates.exchange_rate_info(currency, rate)
        else:
            return "💱 Cotação não disponível para esta moeda.\n\nConsulte nosso suporte para mais informações."
    
    def _generate_default_response(self, conversation: Optional[Conversation]) -> str:
        """
        Gera resposta padrão para mensagens não reconhecidas
        """
        return self.templates.error_message("invalid_option") + "\n\n" + self.templates.menu_options()
    
    def _is_business_hours(self) -> bool:
        """
        Verifica se está dentro do horário comercial
        """
        now = timezone.now()
        weekday = now.strftime('%A').lower()
        
        business_day = self.business_hours.get(weekday)
        if not business_day:
            return False
        
        current_time = now.strftime('%H:%M')
        return business_day['start'] <= current_time <= business_day['end']
    
    def _get_after_hours_message(self) -> str:
        """
        Mensagem para fora do horário comercial
        """
        return "🕐 **FORA DO HORÁRIO COMERCIAL**\n\nNosso atendimento funciona:\n• Segunda a Sexta: 9h às 18h\n• Sábado: 9h às 12h\n• Domingo: Fechado\n\nVocê pode deixar sua mensagem que responderemos assim que possível."
    
    def log_auto_response(self, conversation: Conversation, message_sent: str, trigger: str):
        """
        Registra resposta automática nos logs
        """
        try:
            MessageLog.objects.create(
                conversation=conversation,
                direction="out",
                payload={
                    "text": message_sent,
                    "type": "auto_response",
                    "trigger": trigger,
                    "timestamp": timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Erro ao registrar log de resposta automática: {e}")

# Instância global do handler
auto_message_handler = AutoMessageHandler()