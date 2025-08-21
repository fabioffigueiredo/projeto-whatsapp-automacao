from django.utils import timezone
from decimal import Decimal
import hashlib
import logging
from typing import Dict, Any, Optional, Tuple

from ..models import Conversation, Client, Operation, Transfer
from .fx import dolar_comercial
from .whatsapp import whatsapp_service
from ..authentication import ClientAuthService
from .transfer_service import TransferService
from .xps247 import find_beneficiary_by_cpf

logger = logging.getLogger(__name__)

class ConversationHandler:
    """
    Implementa a árvore de decisão do roteiro WhatsApp para XPS247
    """
    
    def __init__(self):
        pass
    
    def process_message(self, phone: str, message: str) -> str:
        """
        Processa uma mensagem recebida e retorna a resposta
        """
        try:
            # Busca ou cria a conversação
            conversation = self._get_or_create_conversation(phone)
            
            # Processa baseado no estado atual
            response = self._handle_state(conversation, message)
            
            # Log da mensagem recebida
            self._log_message(conversation, "in", {"text": message})
            
            # Log da resposta
            self._log_message(conversation, "out", {"text": response})
            
            return response
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem de {phone}: {str(e)}")
            return "Desculpe, ocorreu um erro. Tente novamente em alguns instantes."
    
    def handle_payment_confirmation(self, operation_id: int, payment_status: str) -> bool:
        """
        Processa confirmação de pagamento e notifica o cliente
        """
        try:
            from ..models import Operation, MessageLog
            
            operation = Operation.objects.get(id=operation_id)
            if not operation.client or not operation.client.phone:
                return False
            
            # Buscar conversa ativa
            conversation = Conversation.objects.filter(
                external_user_id=operation.client.phone
            ).first()
            
            if payment_status == "paid":
                message = f"✅ Pagamento confirmado! Sua transferência de USD {operation.amount_usd} está sendo processada. Você receberá uma confirmação em breve."
                # Atualizar estado da conversa para finalizado
                if conversation:
                    conversation.state_node = "NODE_8_COMPLETED"
                    conversation.context_data = {
                        **conversation.context_data,
                        "operation_id": operation.id,
                        "payment_confirmed": True
                    }
                    conversation.save()
            else:
                message = f"❌ Pagamento não confirmado para sua transferência de USD {operation.amount_usd}. Entre em contato conosco se precisar de ajuda."
                # Atualizar estado da conversa para erro de pagamento
                if conversation:
                    conversation.state_node = "NODE_7_PAYMENT_ERROR"
                    conversation.context_data = {
                        **conversation.context_data,
                        "operation_id": operation.id,
                        "payment_error": True
                    }
                    conversation.save()
            
            # Enviar mensagem via WhatsApp
            whatsapp_service.send_message(operation.client.phone, message)
            
            # Log da mensagem
            if conversation:
                MessageLog.objects.create(
                    conversation=conversation,
                    direction="out",
                    payload={"message": message, "type": "payment_confirmation"}
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling payment confirmation for operation {operation_id}: {e}")
            return False
    
    def _get_or_create_conversation(self, phone: str) -> Conversation:
        """
        Busca ou cria uma conversação para o telefone
        """
        conversation, created = Conversation.objects.get_or_create(
            external_user_id=phone,
            defaults={
                'state_node': 'NODE_1_VERIFICATION',
                'context_data': {},
                'is_active': True
            }
        )
        
        if not created:
            # Atualiza last_seen
            conversation.last_seen = timezone.now()
            conversation.save()
        
        return conversation
    
    def _handle_state(self, conversation: Conversation, message: str) -> str:
        """
        Processa a mensagem baseado no estado atual da conversação
        """
        state = conversation.state_node
        
        # Mapeamento de estados para métodos
        state_handlers = {
            'NODE_1_VERIFICATION': self._handle_node_1_verification,
            'NODE_2_1_EXISTING_CLIENT': self._handle_node_2_1_existing_client,
            'NODE_2_2_NEW_CLIENT': self._handle_node_2_2_new_client,
            'NODE_3_AUTHENTICATION': self._handle_node_3_authentication,
            'NODE_3_PASSWORD': self._handle_node_3_password,
            'NODE_3_AUTH_RETRY': self._handle_node_3_auth_retry,
            'NODE_3_FORGOT_PASSWORD': self._handle_node_3_forgot_password,
            'NODE_4_REGISTRATION': self._handle_node_4_registration,
            'NODE_4_USERNAME': self._handle_node_4_username,
            'NODE_4_COMPLETION': self._handle_node_4_completion,
            'NODE_5_OPERATION_DATA': self._handle_node_5_operation_data,
            'NODE_5_BENEFICIARY_NAME': self._handle_node_5_beneficiary_name,
            'NODE_5_BENEFICIARY_CPF': self._handle_node_5_beneficiary_cpf,
            'NODE_5_BENEFICIARY_REGISTER': self._handle_node_5_beneficiary_register,
            'NODE_5_PIX_KEY': self._handle_node_5_pix_key,
            'NODE_5_ADDRESS': self._handle_node_5_address,
            'NODE_5_AMOUNT': self._handle_node_5_amount,
            'NODE_5_CONFIRMATION': self._handle_node_5_confirmation,
            'NODE_5_CHANGE_OPTIONS': self._handle_node_5_change_options,
            'NODE_6_PAYMENT': self._handle_node_6_payment,
            'NODE_7_NEW_OPERATION': self._handle_node_7_new_operation,
        }
        
        handler = state_handlers.get(state)
        if handler:
            return handler(conversation, message)
        else:
            # Estado desconhecido, reinicia
            conversation.state_node = 'NODE_1_VERIFICATION'
            conversation.context_data = {}
            conversation.save()
            return self._handle_node_1_verification(conversation, message)
    
    def _handle_node_1_verification(self, conversation: Conversation, message: str) -> str:
        """
        Nó 1: Verificação Inicial do Cliente
        """
        phone = conversation.external_user_id
        
        # Verifica se o cliente já existe
        try:
            client = Client.objects.get(phone=phone)
            # Cliente existente
            conversation.state_node = 'NODE_2_1_EXISTING_CLIENT'
            conversation.context_data = {'client_id': client.id}
            conversation.save()
            
            # Busca cotação atual
            rate = dolar_comercial()
            
            return f"Olá, {client.name}! Que bom ter você aqui novamente.\nA cotação do dólar hoje para envio é de R$ {rate:.4f}.\n\nVocê deseja iniciar uma transferência?\n1 - Sim, quero fazer uma transferência\n2 - Não, obrigado"
            
        except Client.DoesNotExist:
            # Novo cliente
            conversation.state_node = 'NODE_2_2_NEW_CLIENT'
            conversation.save()
            
            return "Olá! Bem-vindo(a) à XPS247! 🇺🇸➡️🇧🇷\n\nSua forma rápida e segura de enviar dinheiro dos EUA para o Brasil.\n\nPara começarmos e garantir sua segurança, precisamos realizar um breve cadastro.\nVamos lá?\n\n1 - Sim, quero me cadastrar\n2 - Não agora"
    
    def _handle_node_2_1_existing_client(self, conversation: Conversation, message: str) -> str:
        """
        Nó 2.1: Cliente Existente
        """
        if message.strip() == '1':
            # Cliente quer fazer transferência
            conversation.state_node = 'NODE_3_AUTHENTICATION'
            conversation.save()
            return "Perfeito! 🔐\n\nPara sua segurança, preciso confirmar sua identidade.\nDigite sua senha:"
        elif message.strip() == '2':
            # Cliente não quer fazer transferência agora
            conversation.is_active = False
            conversation.save()
            return "Tudo bem! 😊\n\nQuando quiser fazer uma transferência, é só me chamar.\nTenha um ótimo dia!"
        else:
            return "Por favor, escolha uma opção válida:\n\n1 - Sim, quero fazer uma transferência\n2 - Não, obrigado"
    
    def _handle_node_2_2_new_client(self, conversation: Conversation, message: str) -> str:
        """
        Nó 2.2: Novo Cliente
        """
        message = message.strip()
        
        if message == "1":
            conversation.state_node = 'NODE_4_REGISTRATION'
            conversation.save()
            return "Ótimo! 📝\n\nVamos começar o seu cadastro.\nPara começar, me diga seu nome completo:"
        
        elif message == "2":
            conversation.is_active = False
            conversation.save()
            return "Tudo bem! 😊\n\nQuando estiver pronto para se cadastrar, é só me chamar.\nTenha um ótimo dia!"
        
        else:
            return "Por favor, escolha uma opção válida:\n\n1 - Sim, quero me cadastrar\n2 - Não agora"
    
    def _handle_node_3_authentication(self, conversation: Conversation, message: str) -> str:
        """
        Nó 3: Autenticação - Validação de senha
        """
        client_id = conversation.context_data.get('client_id')
        password = message.strip()
        
        try:
            client = Client.objects.get(id=client_id)
            # Simula verificação de senha (em produção usar hash)
            if password == "123456":  # Senha padrão para simulação
                # Autenticação bem-sucedida
                conversation.state_node = 'NODE_5_OPERATION_DATA'
                conversation.save()
                return "✅ Autenticação realizada com sucesso!\n\nVamos iniciar sua transferência.\nQual o nome completo do destinatário?"
            else:
                # Senha incorreta
                conversation.state_node = 'NODE_3_AUTH_RETRY'
                conversation.save()
                return "❌ Senha incorreta.\n\nO que você gostaria de fazer?\n\n1 - Tentar novamente\n2 - Esqueci minha senha"
                
        except Client.DoesNotExist:
            conversation.is_active = False
            conversation.save()
            return "Erro interno. Por favor, tente novamente mais tarde."
    
    def _handle_node_3_password(self, conversation: Conversation, message: str) -> str:
        """
        Nó 3: Autenticação - Validação de senha
        """
        password = message.strip()
        username_or_email = conversation.context_data.get('auth_username', '')
        
        # Busca o cliente
        client_id = conversation.context_data.get('client_id')
        try:
            client = Client.objects.get(id=client_id)
            
            # Valida credenciais usando ClientAuthService
            auth_service = ClientAuthService()
            authenticated_client = auth_service.authenticate_client(username_or_email, password)
            
            if authenticated_client and authenticated_client.id == client.id:
                # Login válido
                conversation.state_node = 'NODE_5_OPERATION_DATA'
                conversation.save()
                return "Login realizado com sucesso! Vamos iniciar sua transferência.\n\nExcelente! Agora, por favor, informe os dados da pessoa que irá receber o dinheiro no Brasil.\n\n1. Qual o Nome Completo do destinatário?"
            
            else:
                # Credenciais inválidas
                conversation.state_node = 'NODE_3_AUTH_RETRY'
                conversation.save()
                return "Usuário ou senha incorretos.\n1 - Tentar novamente\n2 - Esqueci minha senha"
        
        except Client.DoesNotExist:
            return "Erro interno. Tente novamente."
    
    def _handle_node_3_auth_retry(self, conversation: Conversation, message: str) -> str:
        """
        Nó 3: Opções após falha na autenticação
        """
        option = message.strip()
        
        if option == '1':
            # Tentar novamente
            conversation.state_node = 'NODE_3_AUTHENTICATION'
            conversation.save()
            return "🔐 Digite sua senha novamente:"
        elif option == '2':
            # Esqueci minha senha
            conversation.state_node = 'NODE_3_FORGOT_PASSWORD'
            conversation.save()
            return "📧 Por favor, informe seu e-mail para enviarmos o link de redefinição de senha:"
        else:
            return "Por favor, escolha uma opção válida:\n\n1 - Tentar novamente\n2 - Esqueci minha senha"
    
    def _handle_node_3_forgot_password(self, conversation: Conversation, message: str) -> str:
        """
        Nó 3: Esqueci minha senha
        """
        email = message.strip()
        
        # Implementação simplificada - apenas simula o envio
        conversation.is_active = False
        conversation.save()
        
        return f"✅ Enviamos um link seguro para redefinição de senha para o e-mail {email}.\n\nPor favor, verifique sua caixa de entrada e spam.\nApós criar uma nova senha, volte aqui e me chame para continuar! 😊"
    
    def _handle_node_4_registration(self, conversation: Conversation, message: str) -> str:
        """
        Nó 4: Cadastro - Coleta nome completo
        """
        full_name = message.strip()
        
        if len(full_name) < 3:
            return "Por favor, digite seu nome completo (mínimo 3 caracteres):"
        
        # Salva o nome no contexto
        conversation.context_data['full_name'] = full_name
        conversation.state_node = 'NODE_4_USERNAME'
        conversation.save()
        
        return f"Obrigado, {full_name}! 👋\n\nAgora, escolha um nome de usuário para sua conta:\n(apenas letras, números e underscore)"
    
    def _handle_node_4_username(self, conversation: Conversation, message: str) -> str:
        """
        Nó 4: Cadastro - Coleta username
        """
        username = message.strip()
        
        # Validação básica do username
        if len(username) < 3:
            return "O nome de usuário deve ter pelo menos 3 caracteres. Tente novamente:"
        
        if not username.replace('_', '').isalnum():
            return "O nome de usuário deve conter apenas letras, números e underscore. Tente novamente:"
        
        # Verifica se já existe
        if Client.objects.filter(username=username).exists():
            return "Este nome de usuário já está em uso. Escolha outro:"
        
        # Cria o cliente
        full_name = conversation.context_data.get('full_name', '')
        client = Client.objects.create(
            name=full_name,
            username=username,
            phone=conversation.external_user_id,
            registration_completed=False
        )
        
        conversation.context_data['client_id'] = client.id
        conversation.state_node = 'NODE_4_COMPLETION'
        conversation.save()
        
        return f"Perfeito! ✅\n\nSeu usuário '{username}' foi criado.\n\nAgora você precisa completar seu cadastro em nosso site seguro:\n🔗 https://xps247.com/cadastro\n\nQuando terminar, digite 'Pronto' para continuarmos."
    
    def _handle_node_4_completion(self, conversation: Conversation, message: str) -> str:
        """
        Nó 4: Aguardando confirmação de completion do cadastro
        """
        message_lower = message.strip().lower()
        
        if message_lower in ['pronto', 'finalizado', 'concluído', 'ok']:
            # Marca o cliente como registration_completed
            client_id = conversation.context_data.get('client_id')
            try:
                client = Client.objects.get(id=client_id)
                client.registration_completed = True
                client.save()
                
                conversation.state_node = 'NODE_5_OPERATION_DATA'
                conversation.save()
                
                return "🎉 Excelente! Seu cadastro foi finalizado com sucesso.\n\nAgora vamos iniciar sua primeira transferência.\n\nPor favor, informe o nome completo do destinatário:"
            except Client.DoesNotExist:
                return "Erro interno. Tente novamente."
        else:
            return "⏳ Aguardando você finalizar o cadastro no site.\n\nQuando terminar, digite \"Pronto\" para continuarmos."
    
    def _handle_node_5_operation_data(self, conversation: Conversation, message: str) -> str:
        """
        Nó 5: Início da coleta de dados da operação
        """
        conversation.state_node = 'NODE_5_BENEFICIARY_NAME'
        conversation.save()
        return "1. Qual o Nome Completo do destinatário?"
    
    def _handle_node_5_beneficiary_name(self, conversation: Conversation, message: str) -> str:
        """
        Nó 5: Coleta nome do beneficiário
        """
        beneficiary_name = message.strip()
        
        if len(beneficiary_name) < 3:
            return "Por favor, digite o nome completo do destinatário (mínimo 3 caracteres):"
        
        # Salva no contexto
        if 'transfer_data' not in conversation.context_data:
            conversation.context_data['transfer_data'] = {}
        
        conversation.context_data['transfer_data']['beneficiary_name'] = beneficiary_name
        conversation.context_data['beneficiary_name'] = beneficiary_name
        conversation.state_node = 'NODE_5_BENEFICIARY_CPF'
        conversation.save()
        
        return f"✅ Nome do destinatário: {beneficiary_name}\n\nAgora, digite o CPF do destinatário:\n(apenas números, sem pontos ou traços)"
    
    def _handle_node_5_beneficiary_cpf(self, conversation: Conversation, message: str) -> str:
        """
        Nó 5: Coleta CPF do beneficiário
        """
        cpf = message.strip().replace('.', '').replace('-', '').replace(' ', '')
        
        if not cpf.isdigit() or len(cpf) != 11:
            return "❌ CPF inválido. Por favor, digite apenas os 11 números do CPF:"
        
        # Verifica se o beneficiário existe no sistema XPS247
        beneficiary = find_beneficiary_by_cpf(cpf)
        
        if beneficiary is None:
            # Beneficiário não encontrado, solicita cadastro
            conversation.state_node = 'NODE_5_BENEFICIARY_REGISTER'
            conversation.context_data['pending_beneficiary_cpf'] = cpf
            conversation.save()
            
            return f"❌ CPF {cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]} não encontrado em nosso sistema.\n\n" \
                   f"Para continuar, precisamos cadastrar este beneficiário.\n\n" \
                   f"Deseja prosseguir com o cadastro?\n\n" \
                   f"1 - Sim, cadastrar beneficiário\n" \
                   f"2 - Não, usar outro CPF"
        
        # Beneficiário encontrado, preenche dados automaticamente
        if 'transfer_data' not in conversation.context_data:
            conversation.context_data['transfer_data'] = {}
        
        conversation.context_data['transfer_data']['beneficiary_cpf'] = cpf
        conversation.context_data['beneficiary_cpf'] = cpf
        
        # Se o beneficiário já tem dados cadastrados, preenche automaticamente
        if beneficiary.get('pix_key'):
            conversation.context_data['transfer_data']['pix_key'] = beneficiary['pix_key']
            conversation.context_data['pix_key'] = beneficiary['pix_key']
        
        if beneficiary.get('address'):
            conversation.context_data['transfer_data']['address'] = beneficiary['address']
            conversation.context_data['address'] = beneficiary['address']
        
        conversation.state_node = 'NODE_5_PIX_KEY'
        conversation.save()
        
        return f"✅ CPF confirmado: {cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}\n" \
               f"✅ Beneficiário encontrado: {beneficiary.get('name', 'Nome não disponível')}\n\n" \
               f"Agora, qual a Chave PIX para recebimento?\n" \
               f"(Pode ser CPF, e-mail, telefone ou chave aleatória)"
    
    def _handle_node_5_beneficiary_register(self, conversation: Conversation, message: str) -> str:
        """
        Nó 5: Opções de cadastro do beneficiário
        """
        option = message.strip()
        
        if option == "1":
            # Prosseguir com cadastro
            cpf = conversation.context_data.get('pending_beneficiary_cpf')
            
            if 'transfer_data' not in conversation.context_data:
                conversation.context_data['transfer_data'] = {}
            
            conversation.context_data['transfer_data']['beneficiary_cpf'] = cpf
            conversation.context_data['beneficiary_cpf'] = cpf
            conversation.state_node = 'NODE_5_PIX_KEY'
            conversation.save()
            
            return f"✅ CPF confirmado: {cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}\n\n" \
                   f"Como este é um novo beneficiário, vamos coletar os dados necessários.\n\n" \
                   f"Agora, qual a Chave PIX para recebimento?\n" \
                   f"(Pode ser CPF, e-mail, telefone ou chave aleatória)"
        
        elif option == "2":
            # Voltar para solicitar outro CPF
            conversation.state_node = 'NODE_5_BENEFICIARY_CPF'
            if 'pending_beneficiary_cpf' in conversation.context_data:
                del conversation.context_data['pending_beneficiary_cpf']
            conversation.save()
            
            return "Por favor, digite o CPF do destinatário:\n(apenas números, sem pontos ou traços)"
        
        else:
            return "❌ Opção inválida. Por favor, escolha:\n\n" \
                   "1 - Sim, cadastrar beneficiário\n" \
                   "2 - Não, usar outro CPF"
    
    def _handle_node_5_pix_key(self, conversation: Conversation, message: str) -> str:
        """
        Nó 5: Coleta chave PIX
        """
        pix_key = message.strip()
        
        if len(pix_key) < 3:
            return "❌ Chave PIX inválida. Por favor, informe uma chave PIX válida:"
        
        # Salva no contexto
        if 'transfer_data' not in conversation.context_data:
            conversation.context_data['transfer_data'] = {}
        
        conversation.context_data['transfer_data']['pix_key'] = pix_key
        conversation.context_data['pix_key'] = pix_key
        conversation.state_node = 'NODE_5_ADDRESS'
        conversation.save()
        
        return f"✅ Chave PIX confirmada: {pix_key}\n\nAgora, informe o endereço completo do destinatário:\n📍 Formato: Rua/Avenida, Número, Complemento, Bairro, Cidade - Estado, CEP"
    
    def _handle_node_5_address(self, conversation: Conversation, message: str) -> str:
        """
        Nó 5: Coleta endereço
        """
        address = message.strip()
        
        if len(address) < 10:
            return "❌ Endereço muito curto. Por favor, informe o endereço completo:\n📍 Formato: Rua/Avenida, Número, Complemento, Bairro, Cidade - Estado, CEP"
        
        # Salva no contexto
        if 'transfer_data' not in conversation.context_data:
            conversation.context_data['transfer_data'] = {}
        
        conversation.context_data['transfer_data']['address'] = address
        conversation.context_data['address'] = address
        conversation.state_node = 'NODE_5_AMOUNT'
        conversation.save()
        
        return "✅ Endereço confirmado!\n\n💰 Agora vamos ao valor da transferência:\nQuanto você deseja enviar em DÓLARES (USD)?\n\nExemplo: 100 ou 150.50"
    
    def _handle_node_5_amount(self, conversation: Conversation, message: str) -> str:
        """
        Nó 5: Coleta valor em USD
        """
        try:
            amount_str = message.strip().replace('$', '').replace(',', '.')
            amount_usd = Decimal(amount_str)
            
            if amount_usd <= 0:
                return "❌ Valor inválido. Por favor, informe um valor maior que zero:\nExemplo: 100 ou 150.50"
            
            # Usa o TransferService para calcular valores
            transfer_service = TransferService()
            calculation_data = {
                'amount_usd': amount_usd,
                'beneficiary_name': conversation.context_data.get('beneficiary_name', ''),
                'beneficiary_cpf': conversation.context_data.get('beneficiary_cpf', ''),
                'pix_key': conversation.context_data.get('pix_key', '')
            }
            
            calculation = transfer_service.calculate_transfer(calculation_data)
            
            # Salva no contexto
            if 'transfer_data' not in conversation.context_data:
                conversation.context_data['transfer_data'] = {}
            
            conversation.context_data['transfer_data']['amount_usd'] = str(amount_usd)
            conversation.context_data['amount_usd'] = str(amount_usd)
            conversation.context_data['exchange_rate'] = str(calculation['exchange_rate'])
            conversation.context_data['amount_brl_gross'] = str(calculation['amount_brl_gross'])
            conversation.context_data['service_fee'] = str(calculation['service_fee'])
            conversation.context_data['amount_brl_net'] = str(calculation['amount_brl_net'])
            conversation.state_node = 'NODE_5_CONFIRMATION'
            conversation.save()
            
            # Monta mensagem de confirmação
            beneficiary_name = conversation.context_data.get('beneficiary_name', '')
            beneficiary_cpf = conversation.context_data.get('beneficiary_cpf', '')
            pix_key = conversation.context_data.get('pix_key', '')
            
            return f"📋 **RESUMO DA TRANSFERÊNCIA**\n\n💵 Você envia: USD {amount_usd}\n📈 Cotação: R$ {calculation['exchange_rate']:.4f}\n💰 Valor bruto: R$ {calculation['amount_brl_gross']:.2f}\n🏦 Taxa de serviço: R$ {calculation['service_fee']:.2f}\n✅ **Valor líquido a receber: R$ {calculation['amount_brl_net']:.2f}**\n\n👤 **DESTINATÁRIO:**\n• Nome: {beneficiary_name}\n• CPF: {beneficiary_cpf}\n• Chave PIX: {pix_key}\n\n❓ Os dados estão corretos?\n1 - ✅ Sim, confirmar transferência\n2 - ✏️ Não, quero alterar dados"
            
        except (ValueError, TypeError):
            return "❌ Valor inválido. Digite apenas números:\nExemplo: 100 ou 150.50"
        except Exception as e:
            logger.error(f"Erro ao calcular transferência: {e}")
            return "❌ Erro ao calcular valores. Tente novamente com um valor válido."
    
    def _handle_node_5_confirmation(self, conversation: Conversation, message: str) -> str:
        """
        Nó 5: Confirmação dos dados
        """
        message = message.strip()
        
        if message == "1":
            # Cria a transferência usando o TransferService
            client_id = conversation.context_data.get('client_id')
            
            try:
                client = Client.objects.get(id=client_id)
                transfer_service = TransferService()
                
                transfer_data = {
                    'client_id': client.id,
                    'beneficiary_name': conversation.context_data.get('beneficiary_name', ''),
                    'beneficiary_cpf': conversation.context_data.get('beneficiary_cpf', ''),
                    'pix_key': conversation.context_data.get('pix_key', ''),
                    'beneficiary_address': conversation.context_data.get('address', ''),
                    'amount_usd': Decimal(conversation.context_data.get('amount_usd', '0'))
                }
                
                transfer = transfer_service.create_transfer(transfer_data)
                
                conversation.context_data['transfer_id'] = transfer.id
                conversation.state_node = 'NODE_6_PAYMENT'
                conversation.save()
                
                # Gera link de pagamento
                payment_link = transfer_service.generate_payment_link(transfer.id)
                
                return f"🎉 **TRANSFERÊNCIA CRIADA COM SUCESSO!**\n\n💳 Para finalizar, gerei um link de pagamento seguro para você. Ele é válido por 20 minutos.\n\n🔗 Clique aqui para pagar: {payment_link}\n\n⚡ Após a confirmação do pagamento, o dinheiro será enviado **imediatamente** para o destinatário!\n\n📱 Você receberá uma mensagem automática aqui mesmo assim que o pagamento for processado."
                
            except Client.DoesNotExist:
                return "❌ Erro interno. Tente novamente."
            except Exception as e:
                logger.error(f"Erro ao criar transferência: {e}")
                return "❌ Erro ao processar transferência. Tente novamente."
        
        elif message == "2":
            conversation.state_node = 'NODE_5_CHANGE_OPTIONS'
            conversation.save()
            return "✏️ **O QUE VOCÊ GOSTARIA DE FAZER?**\n\n1 - 📝 Alterar os dados da operação\n2 - ❌ Cancelar e finalizar o atendimento"
        
        else:
            return "Por favor, escolha uma opção válida:\n\n1 - ✅ Sim, confirmar transferência\n2 - ✏️ Não, quero alterar dados"
    
    def _handle_node_5_change_options(self, conversation: Conversation, message: str) -> str:
        """
        Nó 5: Opções de alteração ou cancelamento
        """
        message = message.strip()
        
        if message == "1":
            # Alterar dados da operação - volta para o início da coleta
            conversation.state_node = 'NODE_5_BENEFICIARY_NAME'
            conversation.save()
            return "📝 **VAMOS RECOMEÇAR A COLETA DOS DADOS**\n\n👤 Qual o nome completo do destinatário?"
        elif message == "2":
            # Cancelar e finalizar
            conversation.is_active = False
            conversation.save()
            return "❌ **OPERAÇÃO CANCELADA**\n\n🙏 Obrigado por usar nossos serviços!\n\n👋 Até a próxima!"
        else:
            return "Por favor, escolha uma opção válida:\n\n1 - 📝 Alterar os dados da operação\n2 - ❌ Cancelar e finalizar o atendimento"
    
    def _handle_node_6_payment(self, conversation: Conversation, message: str) -> str:
        """
        Nó 6: Aguardando pagamento
        """
        return "⏳ **AGUARDANDO CONFIRMAÇÃO DO PAGAMENTO**\n\n💳 Estamos monitorando seu pagamento em tempo real.\n\n📱 Você receberá uma notificação automática assim que o pagamento for processado!\n\n⚡ O envio do dinheiro é **imediato** após a confirmação."
    
    def _handle_node_7_new_operation(self, conversation: Conversation, message: str) -> str:
        """
        Nó 7: Pergunta sobre nova operação após pagamento confirmado
        """
        message = message.strip()
        
        if message == "1":
            # Cliente quer fazer outra transferência
            conversation.state_node = 'NODE_5_OPERATION_DATA'
            conversation.save()
            return "🎉 **EXCELENTE! VAMOS INICIAR UMA NOVA TRANSFERÊNCIA**\n\n👤 Por favor, informe os dados da pessoa que irá receber o dinheiro no Brasil.\n\n1. Qual o Nome Completo do destinatário?"
        elif message == "2":
            # Cliente não quer fazer outra transferência
            conversation.is_active = False
            conversation.save()
            return "🙏 **OBRIGADO POR USAR NOSSOS SERVIÇOS!**\n\n⭐ Esperamos ter atendido suas expectativas.\n\n👋 Para futuras transferências, me envie uma mensagem a qualquer momento!"
        else:
            return "Por favor, escolha uma opção válida:\n\n1 - ✅ Sim, fazer outra transferência\n2 - ❌ Não, finalizar agora"
    
    def _log_message(self, conversation: Conversation, direction: str, payload: Dict[str, Any]):
        """
        Registra mensagem no log
        """
        from ..models import MessageLog
        
        MessageLog.objects.create(
            conversation=conversation,
            direction=direction,
            payload=payload
        )
    
    def handle_payment_confirmation(self, transfer_id: int, status: str) -> Optional[str]:
        """
        Processa confirmação de pagamento via webhook
        """
        try:
            transfer = Transfer.objects.get(id=transfer_id)
            transfer_service = TransferService()
            
            if status == 'paid':
                # Atualiza status da transferência
                transfer_service.update_transfer_status(transfer, 'payment_confirmed', 'webhook', 'Pagamento confirmado via webhook')
                
                # Busca a conversação do cliente
                conversation = Conversation.objects.filter(
                    external_user_id=transfer.client.phone,
                    is_active=True
                ).first()
                
                if conversation:
                    conversation.is_active = False
                    conversation.save()
                
                # Cria nova conversação para permitir resposta
                new_conversation = Conversation.objects.create(
                    external_user_id=transfer.client.phone,
                    state_node='NODE_7_NEW_OPERATION',
                    is_active=True,
                    context_data={'client_id': transfer.client.id}
                )
                
                # Envia mensagem de confirmação
                message = f"🎉 **PAGAMENTO CONFIRMADO COM SUCESSO!**\n\n✅ Sua transferência de **${transfer.amount_usd}** foi enviada para:\n👤 **{transfer.beneficiary_name}**\n\n⚡ O dinheiro já está disponível na conta do destinatário!\n\n💫 **DESEJA FAZER UMA NOVA TRANSFERÊNCIA?**\n\n1 - ✅ Sim, fazer outra transferência\n2 - ❌ Não, finalizar atendimento"
                
                # Envia via WhatsApp
                whatsapp_service.send_message(transfer.client.phone, message)
                
                return message
            
            elif status == 'failed':
                # Atualiza status da transferência
                transfer_service.update_transfer_status(transfer, 'failed', 'webhook', 'Pagamento falhou via webhook')
                
                message = "❌ **PAGAMENTO NÃO APROVADO**\n\n😔 Infelizmente seu pagamento não foi processado com sucesso.\n\n🔄 **OPÇÕES DISPONÍVEIS:**\n\n1 - 🔁 Tentar novamente\n2 - 📞 Falar com suporte\n\n💬 Estamos aqui para ajudar!"
                whatsapp_service.send_message(transfer.client.phone, message)
                
                return message
                
        except Transfer.DoesNotExist:
            logger.error(f"Transferência {transfer_id} não encontrada")
        except Exception as e:
            logger.error(f"Erro ao processar confirmação de pagamento: {e}")
            
        return None