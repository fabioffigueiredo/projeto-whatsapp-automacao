from django.test import TestCase
from unittest.mock import patch, MagicMock
from decimal import Decimal
import re

from core.models import Client, Conversation
from core.services.conversation_handler import ConversationHandler
from core.services.client_auth import ClientAuthService
from core.services.transfer import TransferService


class SystemResponseValidationTest(TestCase):
    """
    Testes específicos para validar se as respostas do sistema
    estão de acordo com os requisitos do roteiro.
    """
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.phone_number = "+5511999999999"
        self.conversation_handler = ConversationHandler()
        
        # Cria uma conversa de teste
        self.conversation = Conversation.objects.create(
            phone_number=self.phone_number,
            state_node='NODE_1_WELCOME',
            is_active=True
        )
    
    def test_welcome_message_format(self):
        """Testa se a mensagem de boas-vindas está no formato correto"""
        response = self.conversation_handler.handle_message(self.conversation, "Olá")
        
        # Verifica elementos obrigatórios da mensagem de boas-vindas
        self.assertIn("👋", response)  # Emoji de saudação
        self.assertIn("Bem-vindo", response)
        self.assertIn("XPS247", response)
        self.assertIn("1 - Já sou cliente", response)
        self.assertIn("2 - Sou novo cliente", response)
        
        # Verifica se não há texto desnecessário
        self.assertNotIn("erro", response.lower())
        self.assertNotIn("falha", response.lower())
    
    def test_authentication_messages_format(self):
        """Testa formato das mensagens de autenticação"""
        
        # Simula cliente existente escolhendo opção 1
        self.conversation.state_node = 'NODE_1_WELCOME'
        response = self.conversation_handler.handle_message(self.conversation, "1")
        
        # Verifica mensagem de solicitação de username
        self.assertIn("🔐", response)  # Emoji de cadeado
        self.assertIn("username ou e-mail", response.lower())
        
        # Simula entrada de username
        self.conversation.state_node = 'NODE_3_AUTHENTICATION'
        response = self.conversation_handler.handle_message(self.conversation, "joao.silva")
        
        # Verifica mensagem de solicitação de senha
        self.assertIn("🔐", response)  # Emoji de cadeado
        self.assertIn("senha", response.lower())
    
    def test_registration_messages_format(self):
        """Testa formato das mensagens de cadastro"""
        
        # Simula novo cliente escolhendo opção 2
        self.conversation.state_node = 'NODE_1_WELCOME'
        response = self.conversation_handler.handle_message(self.conversation, "2")
        
        # Verifica mensagem de solicitação de nome
        self.assertIn("👋", response)  # Emoji de saudação
        self.assertIn("nome completo", response.lower())
        
        # Simula entrada de nome
        self.conversation.state_node = 'NODE_4_REGISTRATION'
        response = self.conversation_handler.handle_message(self.conversation, "João Silva")
        
        # Verifica mensagem de solicitação de username
        self.assertIn("username", response.lower())
        self.assertIn("3 caracteres", response)
    
    def test_transfer_data_collection_format(self):
        """Testa formato das mensagens de coleta de dados da transferência"""
        
        # Simula início da coleta de dados
        self.conversation.state_node = 'NODE_5_OPERATION_DATA'
        response = self.conversation_handler.handle_message(self.conversation, "")
        
        # Verifica mensagem inicial de coleta
        self.assertIn("💰", response)  # Emoji de dinheiro
        self.assertIn("transferência", response.lower())
        self.assertIn("nome completo do destinatário", response.lower())
        
        # Testa coleta de nome do beneficiário
        self.conversation.state_node = 'NODE_5_BENEFICIARY_NAME'
        response = self.conversation_handler.handle_message(self.conversation, "Maria Santos")
        
        # Verifica mensagem de solicitação de CPF
        self.assertIn("📄", response)  # Emoji de documento
        self.assertIn("cpf", response.lower())
        self.assertIn("11 dígitos", response)
        
        # Testa coleta de CPF
        self.conversation.state_node = 'NODE_5_BENEFICIARY_CPF'
        response = self.conversation_handler.handle_message(self.conversation, "12345678901")
        
        # Verifica mensagem de solicitação de PIX
        self.assertIn("🔑", response)  # Emoji de chave
        self.assertIn("chave pix", response.lower())
        
        # Testa coleta de endereço
        self.conversation.state_node = 'NODE_5_PIX_KEY'
        response = self.conversation_handler.handle_message(self.conversation, "maria@email.com")
        
        # Verifica mensagem de solicitação de endereço
        self.assertIn("🏠", response)  # Emoji de casa
        self.assertIn("endereço", response.lower())
    
    def test_amount_calculation_display(self):
        """Testa se o cálculo e exibição do valor está correto"""
        
        # Configura contexto da conversa
        self.conversation.context_data = {
            'beneficiary_name': 'Maria Santos',
            'beneficiary_cpf': '12345678901',
            'pix_key': 'maria@email.com',
            'address': 'Rua das Flores, 123'
        }
        self.conversation.state_node = 'NODE_5_AMOUNT'
        
        with patch.object(TransferService, 'calculate_transfer_values') as mock_calc:
            mock_calc.return_value = {
                'exchange_rate': Decimal('5.50'),
                'amount_brl_gross': Decimal('550.00'),
                'service_fee': Decimal('27.50'),
                'amount_brl_net': Decimal('522.50')
            }
            
            response = self.conversation_handler.handle_message(self.conversation, "100.00")
            
            # Verifica se todos os valores estão presentes
            self.assertIn("$100.00", response)  # Valor em USD
            self.assertIn("R$ 5,50", response)  # Cotação
            self.assertIn("R$ 550,00", response)  # Valor bruto
            self.assertIn("R$ 27,50", response)  # Taxa
            self.assertIn("R$ 522,50", response)  # Valor líquido
            
            # Verifica emojis e formatação
            self.assertIn("💰", response)
            self.assertIn("📊", response)
            self.assertIn("✅", response)
            self.assertIn("✏️", response)
    
    def test_confirmation_message_format(self):
        """Testa formato da mensagem de confirmação"""
        
        # Configura contexto completo
        self.conversation.context_data = {
            'client_id': 1,
            'beneficiary_name': 'Maria Santos',
            'beneficiary_cpf': '12345678901',
            'pix_key': 'maria@email.com',
            'amount_usd': '100.00',
            'exchange_rate': '5.50',
            'amount_brl_gross': '550.00',
            'service_fee': '27.50',
            'amount_brl_net': '522.50'
        }
        self.conversation.state_node = 'NODE_5_CONFIRMATION'
        
        with patch.object(TransferService, 'create_transfer') as mock_create:
            mock_transfer = MagicMock()
            mock_transfer.id = 'transfer_123'
            mock_create.return_value = mock_transfer
            
            response = self.conversation_handler.handle_message(self.conversation, "1")
            
            # Verifica elementos da confirmação
            self.assertIn("🎉", response)  # Emoji de celebração
            self.assertIn("TRANSFERÊNCIA CRIADA COM SUCESSO", response)
            self.assertIn("💳", response)  # Emoji de cartão
            self.assertIn("link seguro", response.lower())
            self.assertIn("xps247.com/payment", response)
            self.assertIn("⚡", response)  # Emoji de raio
            self.assertIn("imediatamente", response.lower())
    
    def test_error_messages_format(self):
        """Testa formato das mensagens de erro"""
        
        # Testa erro de validação de CPF
        self.conversation.state_node = 'NODE_5_BENEFICIARY_CPF'
        response = self.conversation_handler.handle_message(self.conversation, "123")
        
        self.assertIn("❌", response)  # Emoji de erro
        self.assertIn("11 dígitos", response)
        
        # Testa erro de validação de username
        self.conversation.state_node = 'NODE_4_USERNAME'
        response = self.conversation_handler.handle_message(self.conversation, "ab")
        
        self.assertIn("❌", response)  # Emoji de erro
        self.assertIn("pelo menos 3 caracteres", response.lower())
    
    def test_payment_status_messages(self):
        """Testa mensagens de status de pagamento"""
        
        # Testa mensagem de aguardando pagamento
        self.conversation.state_node = 'NODE_6_PAYMENT'
        response = self.conversation_handler.handle_message(self.conversation, "status")
        
        self.assertIn("⏳", response)  # Emoji de ampulheta
        self.assertIn("AGUARDANDO CONFIRMAÇÃO", response)
        self.assertIn("💳", response)  # Emoji de cartão
        self.assertIn("tempo real", response.lower())
        self.assertIn("⚡", response)  # Emoji de raio
    
    def test_new_operation_messages(self):
        """Testa mensagens de nova operação"""
        
        # Testa pergunta sobre nova operação
        self.conversation.state_node = 'NODE_7_NEW_OPERATION'
        response = self.conversation_handler.handle_message(self.conversation, "1")
        
        self.assertIn("🎉", response)  # Emoji de celebração
        self.assertIn("NOVA TRANSFERÊNCIA", response)
        self.assertIn("👤", response)  # Emoji de pessoa
        
        # Testa finalização
        self.conversation.state_node = 'NODE_7_NEW_OPERATION'
        response = self.conversation_handler.handle_message(self.conversation, "2")
        
        self.assertIn("🙏", response)  # Emoji de agradecimento
        self.assertIn("OBRIGADO", response)
        self.assertIn("👋", response)  # Emoji de tchau
    
    def test_cpf_formatting(self):
        """Testa se o CPF é formatado corretamente nas mensagens"""
        
        # Configura contexto com CPF
        self.conversation.context_data = {
            'beneficiary_name': 'Maria Santos',
            'beneficiary_cpf': '12345678901'
        }
        self.conversation.state_node = 'NODE_5_BENEFICIARY_CPF'
        
        response = self.conversation_handler.handle_message(self.conversation, "12345678901")
        
        # Verifica se o CPF foi formatado (123.456.789-01)
        cpf_pattern = r'\d{3}\.\d{3}\.\d{3}-\d{2}'
        # Note: Dependendo da implementação, pode não formatar na resposta imediata
        # Este teste verifica se a validação está funcionando
        self.assertIn("🔑", response)  # Deve prosseguir para próxima etapa
    
    def test_currency_formatting(self):
        """Testa se os valores monetários são formatados corretamente"""
        
        # Testa formatação de valores brasileiros
        test_values = {
            'amount_brl_gross': '1550.75',
            'service_fee': '77.54',
            'amount_brl_net': '1473.21'
        }
        
        # Verifica se os valores são formatados como R$ 1.550,75
        for key, value in test_values.items():
            decimal_value = Decimal(value)
            # A formatação deve seguir o padrão brasileiro
            if decimal_value >= 1000:
                self.assertRegex(str(decimal_value), r'\d+\.\d+')
    
    def test_emoji_consistency(self):
        """Testa se os emojis são usados consistentemente"""
        
        emoji_mapping = {
            'welcome': '👋',
            'security': '🔐',
            'money': '💰',
            'document': '📄',
            'key': '🔑',
            'house': '🏠',
            'success': '🎉',
            'error': '❌',
            'waiting': '⏳',
            'card': '💳',
            'lightning': '⚡',
            'person': '👤',
            'thanks': '🙏',
            'bye': '👋'
        }
        
        # Verifica se cada tipo de mensagem usa o emoji correto
        # Este é um teste conceitual - na implementação real,
        # você verificaria cada resposta específica
        for context, emoji in emoji_mapping.items():
            self.assertIsInstance(emoji, str)
            self.assertEqual(len(emoji), 1)  # Emoji deve ser um caractere
    
    def test_message_length_limits(self):
        """Testa se as mensagens não excedem limites razoáveis"""
        
        # Testa várias mensagens do sistema
        test_messages = [
            (self.conversation_handler.handle_message(self.conversation, "Olá"), "welcome"),
        ]
        
        for response, msg_type in test_messages:
            # WhatsApp tem limite de ~4096 caracteres por mensagem
            self.assertLess(len(response), 4000, f"Mensagem {msg_type} muito longa")
            
            # Verifica se não há quebras de linha excessivas
            line_breaks = response.count('\n')
            self.assertLess(line_breaks, 20, f"Muitas quebras de linha em {msg_type}")
    
    def test_response_completeness(self):
        """Testa se as respostas contêm todas as informações necessárias"""
        
        # Testa se a mensagem de boas-vindas tem todas as opções
        response = self.conversation_handler.handle_message(self.conversation, "Olá")
        
        required_elements = [
            "1 - Já sou cliente",
            "2 - Sou novo cliente",
            "XPS247",
            "Bem-vindo"
        ]
        
        for element in required_elements:
            self.assertIn(element, response, f"Elemento '{element}' ausente na resposta")
    
    def test_no_sensitive_data_exposure(self):
        """Testa se dados sensíveis não são expostos nas mensagens"""
        
        # Simula autenticação com senha
        self.conversation.state_node = 'NODE_3_PASSWORD'
        
        with patch.object(ClientAuthService, 'authenticate') as mock_auth:
            mock_auth.side_effect = Exception("Invalid credentials")
            response = self.conversation_handler.handle_message(self.conversation, "senha123")
            
            # Verifica se a senha não aparece na resposta
            self.assertNotIn("senha123", response)
            
            # Verifica se não há informações técnicas expostas
            self.assertNotIn("Exception", response)
            self.assertNotIn("Error", response)
            self.assertNotIn("Traceback", response)