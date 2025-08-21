from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from core.models import Conversation
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["GET"])
def get_last_response(request, phone_number):
    """
    Retorna a última resposta enviada para um número de telefone específico
    """
    try:
        # Buscar a conversa mais recente do usuário
        conversation = Conversation.objects.filter(
            external_user_id=phone_number
        ).order_by('-last_seen').first()
        
        if not conversation:
            return JsonResponse({
                'message': '👋 Olá! Bem-vindo ao XPS247. Como posso ajudá-lo hoje?',
                'state': 'NODE_1_IDENTIFICATION'
            })
        
        # Obter a última resposta baseada no estado atual
        response_message = get_response_for_state(conversation.state_node, conversation)
        
        return JsonResponse({
            'message': response_message,
            'state': conversation.state_node,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter última resposta para {phone_number}: {e}")
        return JsonResponse({
            'message': 'Sistema processou sua mensagem',
            'error': str(e),
            'success': False
        })

def get_response_for_state(state_node, conversation):
    """
    Retorna a mensagem apropriada baseada no estado atual da conversa
    """
    state_messages = {
        'NODE_1_IDENTIFICATION': '👋 Olá! Bem-vindo ao XPS247. Como posso ajudá-lo hoje?',
        'NODE_2_WELCOME': '🎉 Ótimo! Vou ajudá-lo com sua transferência internacional.',
        'NODE_2_1_EXISTING_CLIENT': '🔐 Por favor, faça seu login para continuar.',
        'NODE_2_2_NEW_CLIENT': '📝 Vamos fazer seu cadastro! É rápido e seguro.',
        'NODE_3_AUTHENTICATION': '🔑 Digite sua senha para continuar.',
        'NODE_3_AUTH_RETRY': '❌ Senha incorreta. Tente novamente ou digite "esqueci" para recuperar.',
        'NODE_4_REGISTRATION': '📋 Vamos coletar alguns dados básicos para seu cadastro.',
        'NODE_4_1_NAME': '👤 Por favor, digite seu nome completo:',
        'NODE_4_2_USERNAME': '🆔 Agora crie um nome de usuário:',
        'NODE_4_3_SITE_REGISTRATION': '🌐 Acesse nosso site para finalizar o cadastro: https://xps247.com/register',
        'NODE_5_TRANSFER_DATA': '💰 Agora vamos coletar os dados da sua transferência.',
        'NODE_5_BENEFICIARY_NAME': '👥 Digite o nome completo do beneficiário:',
        'NODE_5_BENEFICIARY_CPF': '📄 Digite o CPF do beneficiário (formato: 000.000.000-00):',
        'NODE_5_BENEFICIARY_REGISTER': '📝 Beneficiário não encontrado. Digite 1 para cadastrar novo beneficiário ou 2 para tentar outro CPF:',
        'NODE_5_PIX_KEY': '🔑 Digite a chave PIX do beneficiário:',
        'NODE_5_ADDRESS': '🏠 Digite o endereço completo do beneficiário:',
        'NODE_5_AMOUNT': '💵 Digite o valor em USD que deseja enviar:',
        'NODE_6_CONFIRMATION': '✅ Confirme os dados da sua transferência.',
        'NODE_6_CHANGE_DATA': '✏️ Qual dado você gostaria de alterar?',
        'NODE_7_PAYMENT': '💳 Processando seu pagamento...',
        'NODE_7_NEW_OPERATION': '🔄 Transferência concluída! Deseja fazer uma nova operação?',
        'NODE_ERROR': '❌ Ocorreu um erro. Tente novamente ou entre em contato conosco.',
        'NODE_PASSWORD_RECOVERY': '🔐 Enviamos instruções para recuperação de senha.',
    }
    
    # Mensagens personalizadas baseadas no contexto
    if state_node == 'NODE_6_CONFIRMATION' and conversation.context_data:
        try:
            context = json.loads(conversation.context_data) if isinstance(conversation.context_data, str) else conversation.context_data
            beneficiary = context.get('beneficiary_name', 'N/A')
            amount = context.get('amount_usd', 'N/A')
            return f"✅ Confirme: Enviar ${amount} USD para {beneficiary}. Digite 1 para confirmar ou 2 para alterar."
        except:
            pass
    
    return state_messages.get(state_node, 'Sistema processou sua mensagem')