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
            
            return f"Olá, {client.name}! Que bom ter você aqui novamente.\nA cotação do dólar hoje para envio é de R$ {rate:.4f}.\n\nVocê deseja iniciar uma transferência?\n1 - Sim\n2 - Não"
            
        except Client.DoesNotExist:
            # Novo cliente
            conversation.state_node = 'NODE_2_2_NEW_CLIENT'
            conversation.save()
            
            return "Olá! Bem-vindo(a) à XPS247, sua forma rápida e segura de enviar dinheiro dos EUA para o Brasil. Para começarmos e garantir sua segurança, precisamos realizar um breve cadastro. Vamos lá?\n1 - Sim, quero me cadastrar\n2 - Não agora"
    
    def _handle_node_2_1_existing_client(self, conversation: Conversation, message: str) -> str:
        """
        Nó 2.1: Mensagem para Cliente Existente
        """
        message = message.strip()
        
        if message == "1":
            conversation.state_node = 'NODE_3_AUTHENTICATION'
            conversation.save()
            return "Para sua segurança, por favor, faça o login.\nInsira seu nome de usuário ou e-mail cadastrado:"
        
        elif message == "2":
            conversation.is_active = False
            conversation.save()
            return "Entendido. Se precisar de ajuda com outro assunto ou quiser falar com um de nossos atendentes, me avise. Obrigado pelo contato!"
        
        else:
            return "Opção inválida. Por favor, digite 1 para iniciar uma transferência ou 2 para cancelar."
    
    def _handle_node_2_2_new_client(self, conversation: Conversation, message: str) -> str:
        """
        Nó 2.2: Mensagem para Novo Cliente
        """
        message = message.strip()
        
        if message == "1":
            conversation.state_node = 'NODE_4_REGISTRATION'
            conversation.save()
            return "Ótimo! Para começar, qual o seu nome completo?"
        
        elif message == "2":
            conversation.is_active = False
            conversation.save()
            return "Tudo bem! Quando estiver pronto, é só me chamar. Salve nosso número para facilitar o contato. Obrigado!"
        
        else:
            return "Opção inválida. Por favor, digite 1 para me cadastrar ou 2 para não agora."
    
    def _handle_node_3_authentication(self, conversation: Conversation, message: str) -> str:
        """
        Nó 3: Autenticação - Coleta username/email
        """
        username_or_email = message.strip()
        
        # Salva o username/email no contexto
        conversation.context_data['auth_username'] = username_or_email
        conversation.state_node = 'NODE_3_PASSWORD'
        conversation.save()
        
        return "Obrigado. Agora, por favor, insira sua senha:"
    
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
            return "Por favor, informe seu username ou e-mail:"
        elif option == '2':
            # Esqueci minha senha
            conversation.state_node = 'NODE_3_FORGOT_PASSWORD'
            conversation.save()
            return "Por favor, informe seu e-mail para enviarmos o link de redefinição de senha:"
        else:
            return "Opção inválida. Digite:\n1 - Tentar novamente\n2 - Esqueci minha senha"
    
    def _handle_node_3_forgot_password(self, conversation: Conversation, message: str) -> str:
        """
        Nó 3: Esqueci minha senha
        """
        email = message.strip()
        
        # Implementação simplificada - apenas simula o envio
        conversation.is_active = False
        conversation.save()
        
        return f"Enviamos um link seguro para redefinição de senha para o e-mail {email}. Por favor, verifique sua caixa de entrada e spam. Após criar uma nova senha, volte aqui e me chame para continuar."
    
    def _handle_node_4_registration(self, conversation: Conversation, message: str) -> str:
        """
        Nó 4: Cadastro - Coleta nome completo
        """
        full_name = message.strip()
        
        if len(full_name) < 3:
            return "Por favor, informe seu nome completo."
        
        conversation.context_data['registration_name'] = full_name
        conversation.state_node = 'NODE_4_USERNAME'
        conversation.save()
        
        return f"Prazer, {full_name}! Agora, por favor, crie um nome de usuário:"
    
    def _handle_node_4_username(self, conversation: Conversation, message: str) -> str:
        """
        Nó 4: Cadastro - Coleta username
        """
        username = message.strip()
        
        if len(username) < 3:
            return "O nome de usuário deve ter pelo menos 3 caracteres."
        
        # Verifica se username já existe
        if Client.objects.filter(username=username).exists():
            return "Este nome de usuário já está em uso. Escolha outro:"
        
        # Cria o cliente usando ClientAuthService
        phone = conversation.external_user_id
        name = conversation.context_data.get('registration_name', '')
        
        auth_service = ClientAuthService()
        client = auth_service.register_client(
            name=name,
            phone=phone,
            username=username
        )
        
        conversation.context_data['client_id'] = client.id
        conversation.state_node = 'NODE_4_COMPLETION'
        conversation.save()
        
        return "Perfeito. Para finalizar o cadastro, precisamos de mais alguns dados em nosso site seguro para cumprir as regulamentações. Por favor, acesse o link abaixo para completar seu perfil.\n\n[Link para a página de cadastro da XPS247]\n\nApós finalizar, volte aqui e digite \"Pronto\" para iniciarmos sua primeira transferência!"
    
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
                
                return "Excelente! Cadastro finalizado com sucesso. Agora vamos iniciar sua primeira transferência.\n\nPor favor, informe os dados da pessoa que irá receber o dinheiro no Brasil.\n\n1. Qual o Nome Completo do destinatário?"
            except Client.DoesNotExist:
                return "Erro interno. Tente novamente."
        else:
            return "Aguardando você finalizar o cadastro no site. Quando terminar, digite \"Pronto\" para continuarmos."
    
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
        name = message.strip()
        
        if len(name) < 3:
            return "Por favor, informe o nome completo do destinatário."
        
        conversation.context_data['beneficiary_name'] = name
        conversation.state_node = 'NODE_5_BENEFICIARY_CPF'
        conversation.save()
        
        return "2. Qual o CPF do destinatário? (Use apenas números)"
    
    def _handle_node_5_beneficiary_cpf(self, conversation: Conversation, message: str) -> str:
        """
        Nó 5: Coleta CPF do beneficiário
        """
        cpf = message.strip().replace('.', '').replace('-', '').replace(' ', '')
        
        if not cpf.isdigit() or len(cpf) != 11:
            return "CPF inválido. Por favor, informe apenas os 11 números do CPF:"
        
        conversation.context_data['beneficiary_cpf'] = cpf
        conversation.state_node = 'NODE_5_PIX_KEY'
        conversation.save()
        
        return "3. Qual a Chave PIX para o recebimento? (Pode ser CPF, e-mail, telefone ou chave aleatória)"
    
    def _handle_node_5_pix_key(self, conversation: Conversation, message: str) -> str:
        """
        Nó 5: Coleta chave PIX
        """
        pix_key = message.strip()
        
        if len(pix_key) < 3:
            return "Por favor, informe uma chave PIX válida."
        
        conversation.context_data['pix_key'] = pix_key
        conversation.state_node = 'NODE_5_ADDRESS'
        conversation.save()
        
        return "4. Por favor, informe o endereço completo do destinatário no formato:\nRua/Avenida, Número, Complemento (se houver), Bairro, Cidade - Estado, CEP"
    
    def _handle_node_5_address(self, conversation: Conversation, message: str) -> str:
        """
        Nó 5: Coleta endereço
        """
        address = message.strip()
        
        if len(address) < 10:
            return "Por favor, informe o endereço completo conforme solicitado."
        
        conversation.context_data['address'] = address
        conversation.state_node = 'NODE_5_AMOUNT'
        conversation.save()
        
        return "Dados do destinatário recebidos! Agora, para o valor:\nQuanto você deseja transferir em DÓLARES (USD)?"
    
    def _handle_node_5_amount(self, conversation: Conversation, message: str) -> str:
        """
        Nó 5: Coleta valor em USD
        """
        try:
            amount_str = message.strip().replace('$', '').replace(',', '.')
            amount_usd = Decimal(amount_str)
            
            if amount_usd <= 0:
                return "Por favor, informe um valor válido maior que zero."
            
            # Usa o TransferService para calcular valores
            transfer_service = TransferService()
            calculation_data = {
                'amount_usd': amount_usd,
                'beneficiary_name': conversation.context_data.get('beneficiary_name', ''),
                'beneficiary_cpf': conversation.context_data.get('beneficiary_cpf', ''),
                'pix_key': conversation.context_data.get('pix_key', '')
            }
            
            calculation = transfer_service.calculate_transfer(calculation_data)
            
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
            
            return f"Por favor, confirme todos os dados da sua operação:\n\nVocê envia: $ {amount_usd}\nCotação do Dólar: R$ {calculation['exchange_rate']:.4f}\nValor bruto: R$ {calculation['amount_brl_gross']:.2f}\nTaxa de serviço: R$ {calculation['service_fee']:.2f}\nValor líquido a receber: R$ {calculation['amount_brl_net']:.2f}\n\nRecebedor:\n• Nome: {beneficiary_name}\n• CPF: {beneficiary_cpf}\n• Chave PIX: {pix_key}\n\nOs dados estão corretos?\n1 - Sim, tudo correto\n2 - Não, quero alterar"
            
        except (ValueError, TypeError):
            return "Valor inválido. Por favor, informe apenas números (ex: 150.00):"
        except Exception as e:
            logger.error(f"Erro ao calcular transferência: {e}")
            return "Erro ao calcular valores. Tente novamente."
    
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
                
                return f"Perfeito! Para finalizar, gerei um link de pagamento seguro para você. Ele é válido por 20 minutos.\n\nClique aqui para pagar: {payment_link}\n\nApós a confirmação do pagamento, você receberá uma mensagem automática aqui mesmo."
                
            except Client.DoesNotExist:
                return "Erro interno. Tente novamente."
            except Exception as e:
                logger.error(f"Erro ao criar transferência: {e}")
                return "Erro ao processar transferência. Tente novamente."
        
        elif message == "2":
            conversation.state_node = 'NODE_5_CHANGE_OPTIONS'
            conversation.save()
            return "O que você gostaria de fazer?\n1 - Alterar os dados da operação\n2 - Cancelar e finalizar o atendimento"
        
        else:
            return "Opção inválida. Digite 1 para confirmar ou 2 para alterar."
    
    def _handle_node_5_change_options(self, conversation: Conversation, message: str) -> str:
        """
        Nó 5: Opções de alteração ou cancelamento
        """
        message = message.strip()
        
        if message == "1":
            # Alterar dados da operação - volta para o início da coleta
            conversation.state_node = 'NODE_5_BENEFICIARY_NAME'
            conversation.save()
            return "Vamos recomeçar a coleta dos dados.\n\n1. Qual o Nome Completo do destinatário?"
        elif message == "2":
            # Cancelar e finalizar
            conversation.is_active = False
            conversation.save()
            return "Operação cancelada. Obrigado por usar nossos serviços! Para iniciar uma nova transferência, me envie uma mensagem."
        else:
            return "Opção inválida. Digite:\n1 - Alterar os dados da operação\n2 - Cancelar e finalizar o atendimento"
    
    def _handle_node_6_payment(self, conversation: Conversation, message: str) -> str:
        """
        Nó 6: Aguardando pagamento
        """
        return "Aguardando confirmação do pagamento. Você receberá uma mensagem automática assim que o pagamento for processado."
    
    def _handle_node_7_new_operation(self, conversation: Conversation, message: str) -> str:
        """
        Nó 7: Pergunta sobre nova operação após pagamento confirmado
        """
        message = message.strip()
        
        if message == "1":
            # Cliente quer fazer outra transferência
            conversation.state_node = 'NODE_5_OPERATION_DATA'
            conversation.save()
            return "Excelente! Vamos iniciar uma nova transferência.\n\nPor favor, informe os dados da pessoa que irá receber o dinheiro no Brasil.\n\n1. Qual o Nome Completo do destinatário?"
        elif message == "2":
            # Cliente não quer fazer outra transferência
            conversation.is_active = False
            conversation.save()
            return "Obrigado por usar nossos serviços! Tenha um ótimo dia. Para futuras transferências, me envie uma mensagem a qualquer momento."
        else:
            return "Opção inválida. Digite:\n1 - Sim, fazer outra transferência\n2 - Não, finalizar agora"
    
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
                message = f"✅ Pagamento Confirmado! Sua transação foi concluída com sucesso.\n\nO dinheiro estará na conta do(a) {transfer.beneficiary_name} em até 1 dia útil. Enviaremos uma nova mensagem assim que o valor for creditado.\n\nDeseja realizar outra transação?\n1 - Sim, fazer outra transferência\n2 - Não, finalizar agora"
                
                # Envia via WhatsApp
                whatsapp_service.send_message(transfer.client.phone, message)
                
                return message
            
            elif status == 'failed':
                # Atualiza status da transferência
                transfer_service.update_transfer_status(transfer, 'failed', 'webhook', 'Pagamento falhou via webhook')
                
                message = "❌ Pagamento não foi processado. Tente novamente ou entre em contato conosco."
                whatsapp_service.send_message(transfer.client.phone, message)
                
                return message
                
        except Transfer.DoesNotExist:
            logger.error(f"Transferência {transfer_id} não encontrada")
        except Exception as e:
            logger.error(f"Erro ao processar confirmação de pagamento: {e}")
            
        return None