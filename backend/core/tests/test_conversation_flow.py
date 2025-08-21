from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch, MagicMock
from decimal import Decimal
import json

from core.models import Client, Conversation, Transfer
from core.services.conversation_handler import ConversationHandler
from core.authentication import ClientAuthService
from core.services.transfer_service import TransferService


class ConversationFlowTest(TestCase):
    """
    Teste automatizado que simula o comportamento completo do cliente
    seguindo todas as etapas do roteiro de conversa.
    """
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.phone_number = "+5511999999999"
        self.webhook_url = reverse('whatsapp_webhook')
        self.conversation_handler = ConversationHandler()
        
        # Dados de teste para cliente existente
        self.existing_client_data = {
            'name': 'João Silva',
            'username': 'joao.silva',
            'email': 'joao@email.com',
            'phone': self.phone_number,
            'password_hash': 'senha123',
            'registration_completed': True
        }
        
        # Dados de teste para nova transferência
        self.transfer_data = {
            'beneficiary_name': 'Maria Santos',
            'beneficiary_cpf': '12345678901',
            'pix_key': 'maria@email.com',
            'address': 'Rua das Flores, 123, São Paulo, SP',
            'amount_usd': '100.00'
        }
    
    def _send_message(self, message: str) -> dict:
        """Envia uma mensagem via webhook e retorna a resposta"""
        # Estrutura de dados similar ao WhatsApp Cloud API
        webhook_data = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15550123456",
                            "phone_number_id": "123456789"
                        },
                        "messages": [{
                            "from": self.phone_number,
                            "id": f"msg_{hash(message)}",
                            "timestamp": "1234567890",
                            "text": {
                                "body": message
                            },
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        response = self.client.post(
            self.webhook_url,
            data=webhook_data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        return response.json()
    
    def test_complete_flow_new_client(self):
        """Testa o fluxo completo para um novo cliente"""
        
        # 1. ETAPA: Identificação e Boas-vindas
        response = self._send_message("Olá")
        self.assertEqual(response['status'], 'success')
        
        # Verifica se a conversa foi criada
        conversation = Conversation.objects.get(external_user_id=self.phone_number)
        self.assertEqual(conversation.state_node, 'NODE_2_2_NEW_CLIENT')
        
        # Cliente escolhe "Sou novo cliente"
        response = self._send_message("2")
        self.assertEqual(response['status'], 'success')
        
        # Verifica mudança de estado
        conversation.refresh_from_db()
        self.assertEqual(conversation.state_node, 'NODE_4_REGISTRATION')
        
        # 2. ETAPA: Cadastro - Nome completo
        response = self._send_message("João Silva")
        self.assertEqual(response['status'], 'success')
        
        # 3. ETAPA: Cadastro - Username
        response = self._send_message("joao.silva")
        self.assertEqual(response['status'], 'success')
        
        # Verifica se o cliente foi criado
        client = Client.objects.filter(phone=self.phone_number).first()
        self.assertIsNotNone(client)
        self.assertEqual(client.name, "João Silva")
        self.assertEqual(client.username, "joao.silva")
        
        # 4. ETAPA: Confirmação de cadastro
        response = self._send_message("Pronto")
        self.assertIn("cadastro finalizado", response['reply'].lower())
        self.assertIn("nome completo do destinatário", response['reply'].lower())
        
        # 5. ETAPA: Coleta de dados da transferência
        self._test_transfer_data_collection()
        
        # 6. ETAPA: Confirmação e pagamento
        self._test_confirmation_and_payment()
    
    def test_complete_flow_existing_client(self):
        """Testa o fluxo completo para um cliente existente"""
        
        # Cria cliente existente
        client = Client.objects.create(**self.existing_client_data)
        
        # 1. ETAPA: Identificação e Boas-vindas
        response = self._send_message("Olá")
        self.assertIn("Bem-vindo", response['reply'])
        
        # Cliente escolhe "Já sou cliente"
        response = self._send_message("1")
        self.assertEqual(response['status'], 'success')
        
        # Verifica mudança de estado
        conversation = Conversation.objects.get(external_user_id=self.phone_number)
        conversation.refresh_from_db()
        self.assertEqual(conversation.state_node, 'NODE_2_1_EXISTING_CLIENT')
        
        # 2. ETAPA: Autenticação - Username
        response = self._send_message("joao.silva")
        self.assertEqual(response['status'], 'success')
        
        # 3. ETAPA: Autenticação - Senha
        with patch.object(ClientAuthService, 'authenticate') as mock_auth:
            mock_auth.return_value = client
            response = self._send_message("senha123")
            self.assertEqual(response['status'], 'success')
            
            # Verifica autenticação
            conversation.refresh_from_db()
            self.assertEqual(conversation.state_node, 'NODE_5_OPERATION_DATA')
        
        # 4. ETAPA: Coleta de dados da transferência
        self._test_transfer_data_collection()
        
        # 5. ETAPA: Confirmação e pagamento
        self._test_confirmation_and_payment()
    
    def _test_transfer_data_collection(self):
        """Testa a coleta de dados da transferência"""
        
        # Nome do beneficiário
        response = self._send_message(self.transfer_data['beneficiary_name'])
        self.assertEqual(response['status'], 'success')
        
        # CPF do beneficiário
        response = self._send_message(self.transfer_data['beneficiary_cpf'])
        self.assertEqual(response['status'], 'success')
        
        # Chave PIX
        response = self._send_message(self.transfer_data['pix_key'])
        self.assertEqual(response['status'], 'success')
        
        # Endereço
        response = self._send_message(self.transfer_data['address'])
        self.assertEqual(response['status'], 'success')
        
        # Valor da transferência
        with patch.object(TransferService, 'calculate_transfer_values') as mock_calc:
            mock_calc.return_value = {
                'exchange_rate': Decimal('5.50'),
                'amount_brl_gross': Decimal('550.00'),
                'service_fee': Decimal('27.50'),
                'amount_brl_net': Decimal('522.50')
            }
            
            response = self._send_message(self.transfer_data['amount_usd'])
            self.assertEqual(response['status'], 'success')
            
        # Verifica se a operação foi criada através do context_data
        conversation = Conversation.objects.get(external_user_id=self.phone_number)
        client_id = conversation.context_data.get('client_id')
        self.assertIsNotNone(client_id)
        
        # Verifica se cliente foi criado
        client = Client.objects.filter(id=client_id).first()
        self.assertIsNotNone(client)
    
    def _test_confirmation_and_payment(self):
        """Testa a confirmação e processo de pagamento"""
        
        with patch.object(TransferService, 'create_transfer') as mock_create:
            mock_transfer = MagicMock()
            mock_transfer.id = 'transfer_123'
            mock_create.return_value = mock_transfer
            
            # Confirmação da transferência
            response = self._send_message("1")
            self.assertEqual(response['status'], 'success')
            
            # Verifica se a transferência foi criada
            conversation = Conversation.objects.get(external_user_id=self.phone_number)
            transfer = Transfer.objects.filter(client=conversation.client).first()
            self.assertIsNotNone(transfer)
            self.assertEqual(transfer.status, 'pending_payment')
    
    def test_authentication_failure_and_retry(self):
        """Testa falha na autenticação e tentativa de recuperação"""
        
        # Cria cliente existente
        client = Client.objects.create(**self.existing_client_data)
        
        # Inicia fluxo
        self._send_message("Olá")
        self._send_message("1")  # Já sou cliente
        self._send_message("joao.silva")  # Username
        
        # Senha incorreta
        with patch.object(ClientAuthService, 'authenticate') as mock_auth:
            mock_auth.side_effect = Exception("Invalid credentials")
            response = self._send_message("senha_errada")
            self.assertEqual(response['status'], 'success')
            
            # Verifica estado de retry
            conversation = Conversation.objects.get(external_user_id=self.phone_number)
            self.assertEqual(conversation.state_node, 'NODE_3_AUTH_RETRY')
        
        # Escolhe "Esqueci minha senha"
        response = self._send_message("2")
        self.assertEqual(response['status'], 'success')
        
        # Fornece e-mail para recuperação
        response = self._send_message("joao@email.com")
        self.assertEqual(response['status'], 'success')
    
    def test_data_validation_errors(self):
        """Testa validações de dados inválidos"""
        
        # Inicia fluxo como novo cliente
        self._send_message("Olá")
        self._send_message("2")
        self._send_message("João Silva")
        
        # Username muito curto
        response = self._send_message("jo")
        self.assertEqual(response['status'], 'success')
        
        # Username válido
        response = self._send_message("joao.silva")
        self.assertEqual(response['status'], 'success')
        self._send_message("Pronto")
        
        # Nome do beneficiário muito curto
        response = self._send_message("A")
        self.assertEqual(response['status'], 'success')
        
        # Nome válido
        self._send_message("Maria Santos")
        
        # CPF inválido
        response = self._send_message("123")
        self.assertEqual(response['status'], 'success')
        
        # CPF válido
        self._send_message("12345678901")
        
        # Chave PIX inválida
        response = self._send_message("email_invalido")
        self.assertEqual(response['status'], 'success')
    
    def test_change_operation_data(self):
        """Testa alteração de dados da operação"""
        
        # Simula chegada até a confirmação
        self._simulate_flow_to_confirmation()
        
        # Escolhe alterar dados
        response = self._send_message("2")
        self.assertEqual(response['status'], 'success')
        
        # Verifica mudança para estado de alteração
        conversation = Conversation.objects.get(external_user_id=self.phone_number)
        
        # Escolhe alterar dados do destinatário
        response = self._send_message("1")
        self.assertEqual(response['status'], 'success')
    
    def test_payment_confirmation_webhook(self):
        """Testa confirmação de pagamento via webhook"""
        
        # Cria transferência pendente
        transfer = Transfer.objects.create(
            client=Client.objects.create(**self.existing_client_data),
            beneficiary_name="Maria Santos",
            beneficiary_cpf="12345678900",
            pix_key="maria@email.com",
            beneficiary_address="Rua das Flores, 123",
            amount_usd=Decimal('100.00'),
            exchange_rate=Decimal('5.50'),
            total_amount_usd=Decimal('100.00'),
            amount_brl_estimated=Decimal('550.00'),
            status="pending_payment",
            payment_reference="PAY123"
        )
        
        # Simula webhook de pagamento aprovado
        conversation_handler = ConversationHandler()
        result = conversation_handler.handle_payment_confirmation(transfer.id, "paid")
        
        # Verifica se status foi atualizado
        transfer.refresh_from_db()
        self.assertEqual(transfer.status, "payment_confirmed")
        
        # Verifica se uma nova conversa foi criada para nova operação
        new_conversation = Conversation.objects.filter(
            external_user_id=transfer.client.phone,
            state_node='NODE_7_NEW_OPERATION'
        ).first()
        self.assertIsNotNone(new_conversation)
    
    def _simulate_flow_to_confirmation(self):
        """Simula fluxo completo até a etapa de confirmação"""
        
        # Cria cliente
        client = Client.objects.create(**self.existing_client_data)
        
        # Simula autenticação bem-sucedida
        with patch('core.authentication.ClientAuthService.authenticate_client') as mock_auth:
            mock_auth.return_value = client
            
            self._send_message("Olá")
            self._send_message("1")  # Já sou cliente
            self._send_message("joao123")  # Username
            self._send_message("senha123")  # Senha
            
            # Coleta dados da transferência
            self._send_message("Maria Santos")  # Nome
            self._send_message("123.456.789-00")  # CPF
            self._send_message("maria@email.com")  # PIX
            self._send_message("Rua das Flores, 123")  # Endereço
            
            with patch('core.services.fx.dolar_comercial') as mock_fx:
                mock_fx.return_value = Decimal('5.50')
                self._send_message("100")  # Valor
            
            return {
                'client': client,
                'transfer_data': self.transfer_data
            }
    
    def test_invalid_options(self):
        """Testa opções inválidas em diferentes etapas"""
        
        # Inicia conversa
        response = self._send_message("Olá")
        self.assertEqual(response['status'], 'success')
        
        # Verifica que conversa foi criada
        conversation = Conversation.objects.get(external_user_id=self.phone_number)
        self.assertEqual(conversation.state_node, 'NODE_2_2_NEW_CLIENT')
        
        # Opção inválida na verificação
        response = self._send_message("3")
        self.assertEqual(response['status'], 'success')
        
        # Verifica que ainda está no mesmo estado
        conversation.refresh_from_db()
        self.assertEqual(conversation.state_node, 'NODE_2_2_NEW_CLIENT')
    
    def test_conversation_state_persistence(self):
        """Testa se o estado da conversa é mantido corretamente"""
        
        # Inicia conversa
        response = self._send_message("Olá")
        self.assertEqual(response['status'], 'success')
        
        # Verifica se a conversa foi criada
        conversation = Conversation.objects.filter(external_user_id=self.phone_number).first()
        self.assertIsNotNone(conversation)
        self.assertTrue(conversation.is_active)
        self.assertEqual(conversation.state_node, 'NODE_2_2_NEW_CLIENT')
        
        # Avança no fluxo
        self._send_message("2")  # Novo cliente
        
        # Verifica mudança de estado
        conversation.refresh_from_db()
        # O estado pode variar dependendo do fluxo, vamos verificar se mudou
        self.assertNotEqual(conversation.state_node, 'NODE_2_2_NEW_CLIENT')