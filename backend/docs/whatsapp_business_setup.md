# Configuração do WhatsApp Business API

Este guia explica como configurar o WhatsApp Business API para produção.

## Pré-requisitos

1. **Conta Facebook Business Manager**
   - Acesse [business.facebook.com](https://business.facebook.com)
   - Crie ou acesse sua conta Business Manager

2. **WhatsApp Business Account**
   - Crie uma conta WhatsApp Business no Business Manager
   - Verifique seu número de telefone comercial

3. **Aplicativo Facebook**
   - Crie um aplicativo no [developers.facebook.com](https://developers.facebook.com)
   - Adicione o produto "WhatsApp Business API"

## Passo a Passo da Configuração

### 1. Configurar o Aplicativo Facebook

1. Acesse [developers.facebook.com/apps](https://developers.facebook.com/apps)
2. Clique em "Criar App"
3. Selecione "Business" como tipo de app
4. Preencha as informações básicas:
   - Nome do app
   - Email de contato
   - Conta Business Manager

### 2. Adicionar WhatsApp Business API

1. No painel do app, clique em "Adicionar Produto"
2. Encontre "WhatsApp Business API" e clique em "Configurar"
3. Selecione sua conta WhatsApp Business
4. Configure o número de telefone

### 3. Obter Credenciais

#### Token de Acesso Permanente
1. Vá para "WhatsApp > Introdução"
2. Clique em "Gerar Token"
3. Selecione as permissões necessárias:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
4. Copie o token gerado

#### IDs Necessários
- **App ID**: Encontrado em "Configurações > Básico"
- **App Secret**: Encontrado em "Configurações > Básico"
- **Phone Number ID**: Encontrado em "WhatsApp > Introdução"
- **Business Account ID**: Encontrado em "WhatsApp > Introdução"

### 4. Configurar Webhook

1. Vá para "WhatsApp > Configuração"
2. Na seção "Webhook", clique em "Configurar"
3. Preencha:
   - **URL do Callback**: `https://seu-dominio.com/api/webhook/whatsapp`
   - **Token de Verificação**: Um token único que você definir
4. Selecione os eventos:
   - `messages`
   - `message_deliveries`
   - `message_reads`
   - `message_reactions`

### 5. Configurar Variáveis de Ambiente

Crie um arquivo `.env` baseado no `.env.example` e preencha:

```bash
# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=seu_token_permanente_aqui
WHATSAPP_PHONE_NUMBER_ID=seu_phone_number_id_aqui
WHATSAPP_BUSINESS_ACCOUNT_ID=seu_business_account_id_aqui
WHATSAPP_APP_ID=seu_app_id_aqui
WHATSAPP_APP_SECRET=seu_app_secret_aqui
WHATSAPP_VERIFY_TOKEN=seu_token_verificacao_unico
WHATSAPP_WEBHOOK_URL=https://seu-dominio.com/api/webhook/whatsapp
WHATSAPP_API_VERSION=v18.0
```

### 6. Testar a Configuração

#### Verificar Webhook
1. Execute o servidor Django
2. Use ngrok ou similar para expor localmente (desenvolvimento)
3. Configure a URL do webhook no Facebook
4. Verifique se o webhook é validado com sucesso

#### Enviar Mensagem de Teste
```python
from core.services.whatsapp_business_service import WhatsAppBusinessService

service = WhatsAppBusinessService()
result = service.send_text_message(
    to="5511999999999",  # Número com código do país
    message="Olá! Esta é uma mensagem de teste."
)
print(result)
```

## Configurações de Produção

### 1. Segurança

- **HTTPS Obrigatório**: O webhook deve usar HTTPS
- **Validação de Assinatura**: Sempre validar assinaturas em produção
- **Rate Limiting**: Implementar limitação de taxa
- **Logs**: Configurar logs detalhados

### 2. Monitoramento

```python
# Adicionar ao settings.py
LOGGING = {
    'loggers': {
        'whatsapp_business': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### 3. Backup e Recuperação

- Fazer backup das configurações
- Documentar todos os IDs e tokens
- Ter um plano de recuperação de desastres

## Limites e Quotas

### Limites da API
- **Rate Limit**: 1000 mensagens por segundo
- **Mensagens por dia**: Varia conforme o nível da conta
- **Tipos de mídia**: Imagens, documentos, áudio, vídeo

### Níveis de Conta
1. **Nível 1**: 1.000 conversas em 24h
2. **Nível 2**: 10.000 conversas em 24h
3. **Nível 3**: 100.000 conversas em 24h
4. **Nível 4**: Ilimitado

## Troubleshooting

### Problemas Comuns

#### Webhook não recebe mensagens
1. Verificar se a URL está acessível
2. Confirmar se o token de verificação está correto
3. Verificar logs do servidor
4. Testar com ferramentas como Postman

#### Erro de autenticação
1. Verificar se o token não expirou
2. Confirmar permissões do token
3. Verificar se o App ID está correto

#### Mensagens não são enviadas
1. Verificar se o número está no formato correto
2. Confirmar se o número está registrado no WhatsApp
3. Verificar limites de rate
4. Verificar status da conta Business

### Logs Úteis

```python
import logging

logger = logging.getLogger('whatsapp_business')

# Log de mensagem enviada
logger.info(f"Mensagem enviada para {phone_number}: {message_id}")

# Log de erro
logger.error(f"Erro ao enviar mensagem: {error_message}")

# Log de webhook recebido
logger.info(f"Webhook recebido: {webhook_data}")
```

## Recursos Adicionais

- [Documentação Oficial](https://developers.facebook.com/docs/whatsapp)
- [WhatsApp Business API Reference](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Webhook Reference](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks)
- [Rate Limits](https://developers.facebook.com/docs/whatsapp/cloud-api/overview#rate-limits)

## Suporte

Para problemas técnicos:
1. Verificar logs da aplicação
2. Consultar documentação oficial
3. Usar o Facebook Developer Support
4. Verificar status da API no [Facebook Status](https://developers.facebook.com/status/)