from typing import Dict, List, Any, Optional
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MessageTemplates:
    """
    Classe para gerenciar templates de mensagens do WhatsApp Business
    """
    
    @staticmethod
    def welcome_message(customer_name: str = "Cliente") -> str:
        """
        Mensagem de boas-vindas
        """
        return f"""Olá {customer_name}! 👋

Seja bem-vindo(a) ao nosso atendimento automatizado!

Eu sou seu assistente virtual e estou aqui para ajudá-lo(a) com:
• Consultas de câmbio 💱
• Transferências internacionais 🌍
• Informações sobre nossos serviços 📋

Digite *menu* para ver todas as opções disponíveis.

Como posso ajudá-lo(a) hoje?"""
    
    @staticmethod
    def menu_options() -> str:
        """
        Menu principal de opções
        """
        return """📋 *MENU PRINCIPAL*

Escolha uma das opções abaixo:

1️⃣ *Cotação* - Consultar taxa de câmbio
2️⃣ *Transferência* - Enviar dinheiro para o exterior
3️⃣ *Consultar* - Verificar status de operação
4️⃣ *Suporte* - Falar com atendente humano
5️⃣ *Sobre* - Informações da empresa

Digite o *número* da opção desejada ou a *palavra-chave* em destaque."""
    
    @staticmethod
    def exchange_rate_info(currency: str, rate: float, amount: float = None) -> str:
        """
        Informações de taxa de câmbio
        """
        base_message = f"""💱 *COTAÇÃO {currency.upper()}*

📈 Taxa atual: R$ {rate:.4f}
🕐 Atualizada em: {settings.TIME_ZONE}
"""
        
        if amount:
            converted = amount * rate
            base_message += f"\n💰 {currency.upper()} {amount:.2f} = R$ {converted:.2f}"
        
        base_message += "\n\n⚠️ *Importante:* Taxas podem variar. Consulte nossa equipe para cotação oficial."
        
        return base_message
    
    @staticmethod
    def transfer_instructions() -> str:
        """
        Instruções para transferência
        """
        return """🌍 *TRANSFERÊNCIA INTERNACIONAL*

Para realizar uma transferência, preciso das seguintes informações:

📋 *Dados do Remetente:*
• Nome completo
• CPF
• Telefone

🎯 *Dados do Destinatário:*
• Nome completo
• País de destino
• Dados bancários

💰 *Dados da Operação:*
• Valor a enviar
• Moeda de destino
• Finalidade da remessa

Digite *iniciar transferencia* para começar o processo."""
    
    @staticmethod
    def operation_status(operation_id: str, status: str, amount: float, currency: str) -> str:
        """
        Status de operação
        """
        status_emoji = {
            'pending': '⏳',
            'processing': '🔄',
            'completed': '✅',
            'cancelled': '❌',
            'failed': '⚠️'
        }
        
        status_text = {
            'pending': 'Pendente',
            'processing': 'Em processamento',
            'completed': 'Concluída',
            'cancelled': 'Cancelada',
            'failed': 'Falhou'
        }
        
        emoji = status_emoji.get(status, '📋')
        status_name = status_text.get(status, status.title())
        
        return f"""📊 *STATUS DA OPERAÇÃO*

🆔 ID: {operation_id}
{emoji} Status: {status_name}
💰 Valor: {currency.upper()} {amount:.2f}

Para mais detalhes, entre em contato com nossa equipe."""
    
    @staticmethod
    def error_message(error_type: str = "general") -> str:
        """
        Mensagens de erro
        """
        error_messages = {
            "general": "❌ Ops! Algo deu errado. Tente novamente em alguns instantes.",
            "invalid_option": "⚠️ Opção inválida. Digite *menu* para ver as opções disponíveis.",
            "missing_data": "📝 Informações incompletas. Verifique os dados e tente novamente.",
            "service_unavailable": "🔧 Serviço temporariamente indisponível. Tente novamente mais tarde.",
            "rate_limit": "⏰ Muitas tentativas. Aguarde alguns minutos antes de tentar novamente."
        }
        
        return error_messages.get(error_type, error_messages["general"])
    
    @staticmethod
    def human_support() -> str:
        """
        Transferência para atendimento humano
        """
        return """👨‍💼 *ATENDIMENTO HUMANO*

Você será transferido(a) para um de nossos especialistas.

⏰ *Horário de atendimento:*
Segunda a Sexta: 9h às 18h
Sábado: 9h às 12h

📞 *Contatos diretos:*
Telefone: (11) 1234-5678
Email: atendimento@empresa.com

Aguarde, em breve um atendente entrará em contato."""
    
    @staticmethod
    def company_info() -> str:
        """
        Informações da empresa
        """
        return """🏢 *SOBRE NÓS*

Somos especialistas em câmbio e transferências internacionais, oferecendo:

✅ Taxas competitivas
✅ Segurança total
✅ Atendimento personalizado
✅ Rapidez nas operações

📍 *Endereço:*
Rua Exemplo, 123 - São Paulo/SP

🌐 *Website:*
www.empresa.com.br

📱 *Redes sociais:*
@empresa_oficial

Autorizada pelo Banco Central do Brasil."""
    
    @staticmethod
    def create_button_template(header_text: str, body_text: str, buttons: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Cria template de mensagem com botões
        
        Args:
            header_text: Texto do cabeçalho
            body_text: Texto do corpo
            buttons: Lista de botões [{'id': 'btn1', 'title': 'Botão 1'}, ...]
            
        Returns:
            Dict com estrutura da mensagem interativa
        """
        if len(buttons) > 3:
            raise ValueError("Máximo de 3 botões permitidos")
        
        button_components = []
        for i, button in enumerate(buttons):
            button_components.append({
                "type": "button",
                "sub_type": "quick_reply",
                "index": str(i),
                "parameters": [{
                    "type": "payload",
                    "payload": button.get('id', f'btn_{i}')
                }, {
                    "type": "text",
                    "text": button.get('title', f'Opção {i+1}')
                }]
            })
        
        return {
            "type": "button",
            "header": {
                "type": "text",
                "text": header_text
            },
            "body": {
                "text": body_text
            },
            "action": {
                "buttons": button_components
            }
        }
    
    @staticmethod
    def create_list_template(header_text: str, body_text: str, button_text: str, 
                           sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Cria template de mensagem com lista
        
        Args:
            header_text: Texto do cabeçalho
            body_text: Texto do corpo
            button_text: Texto do botão da lista
            sections: Lista de seções com opções
            
        Returns:
            Dict com estrutura da mensagem interativa
        """
        return {
            "type": "list",
            "header": {
                "type": "text",
                "text": header_text
            },
            "body": {
                "text": body_text
            },
            "action": {
                "button": button_text,
                "sections": sections
            }
        }
    
    @staticmethod
    def create_currency_list() -> Dict[str, Any]:
        """
        Cria lista de moedas disponíveis
        """
        currencies = [
            {"id": "USD", "title": "Dólar Americano (USD)", "description": "Estados Unidos"},
            {"id": "EUR", "title": "Euro (EUR)", "description": "União Europeia"},
            {"id": "GBP", "title": "Libra Esterlina (GBP)", "description": "Reino Unido"},
            {"id": "CAD", "title": "Dólar Canadense (CAD)", "description": "Canadá"},
            {"id": "AUD", "title": "Dólar Australiano (AUD)", "description": "Austrália"},
            {"id": "JPY", "title": "Iene Japonês (JPY)", "description": "Japão"},
        ]
        
        sections = [{
            "title": "Moedas Disponíveis",
            "rows": currencies
        }]
        
        return MessageTemplates.create_list_template(
            "💱 Cotação de Moedas",
            "Selecione a moeda para consultar a cotação atual:",
            "Ver Moedas",
            sections
        )
    
    @staticmethod
    def create_service_menu() -> Dict[str, Any]:
        """
        Cria menu de serviços com botões
        """
        buttons = [
            {"id": "cotacao", "title": "💱 Cotação"},
            {"id": "transferencia", "title": "🌍 Transferência"},
            {"id": "suporte", "title": "👨‍💼 Suporte"}
        ]
        
        return MessageTemplates.create_button_template(
            "🏢 Nossos Serviços",
            "Como podemos ajudá-lo hoje? Escolha uma das opções abaixo:",
            buttons
        )
    
    @staticmethod
    def payment_confirmation(amount: float, currency: str, recipient: str, 
                           payment_link: str) -> str:
        """
        Confirmação de pagamento
        """
        return f"""💳 *CONFIRMAÇÃO DE PAGAMENTO*

💰 Valor: {currency.upper()} {amount:.2f}
👤 Destinatário: {recipient}

🔗 *Link para pagamento:*
{payment_link}

⚠️ *Importante:*
• Link válido por 24 horas
• Pagamento seguro via cartão ou PIX
• Você receberá confirmação por email

Após o pagamento, sua transferência será processada em até 2 dias úteis."""
    
    @staticmethod
    def operation_receipt(operation_id: str, amount: float, currency: str, 
                         recipient: str, fee: float) -> str:
        """
        Comprovante de operação
        """
        total = amount + fee
        
        return f"""🧾 *COMPROVANTE DE OPERAÇÃO*

🆔 ID: {operation_id}
💰 Valor: {currency.upper()} {amount:.2f}
💳 Taxa: R$ {fee:.2f}
📊 Total: R$ {total:.2f}
👤 Destinatário: {recipient}
📅 Data: {settings.TIME_ZONE}

✅ Operação registrada com sucesso!

Você receberá atualizações sobre o status da transferência.

Guarde este comprovante para suas consultas."""

# Instância global dos templates
message_templates = MessageTemplates()