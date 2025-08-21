# 🚀 Guia de Configuração WhatsApp Business API

## 📋 Pré-requisitos

### 1. Conta Meta for Developers
- Acesse: https://developers.facebook.com/
- Crie uma conta ou faça login
- Aceite os termos de uso

### 2. Verificação de Negócio
- Empresa verificada no Meta Business Manager
- Número de telefone comercial válido
- Documentos da empresa (CNPJ, etc.)

## 🔧 Configuração Passo a Passo

### Etapa 1: Criar Aplicativo

1. **Acesse Meta for Developers**
   ```
   https://developers.facebook.com/apps/
   ```

2. **Criar Novo App**
   - Clique em "Criar App"
   - Selecione "Negócios"
   - Nome do app: "WhatsApp Automação"
   - Email de contato: seu email

3. **Adicionar WhatsApp Business**
   - No painel do app, clique em "+ Adicionar produto"
   - Selecione "WhatsApp Business"
   - Clique em "Configurar"

### Etapa 2: Configurar Webhook

1. **URL do Webhook**
   ```
   https://seu-dominio.com/api/webhook/
   ```
   
   **Para desenvolvimento local (usando ngrok):**
   ```bash
   # Instalar ngrok
   npm install -g ngrok
   
   # Expor porta 8001 (porta do Django)
   ngrok http 8001

   # Use a URL gerada: https://abc123.ngrok.io/api/webhook/
   ```

2. **Token de Verificação**
   ```
   whatsapp_verify_token_123
   ```

3. **Campos de Webhook**
   - ✅ messages
   - ✅ message_deliveries
   - ✅ message_reads
   - ✅ message_reactions

### Etapa 3: Obter Tokens

1. **Token de Acesso Temporário**
   - No painel WhatsApp Business
   - Copie o token temporário (válido por 24h)

2. **Token de Acesso Permanente**
   ```bash
   curl -X GET "https://graph.facebook.com/v18.0/oauth/access_token" \
     -d "grant_type=client_credentials" \
     -d "client_id=SEU_APP_ID" \
     -d "client_secret=SEU_APP_SECRET"
   ```

3. **Phone Number ID**
   - Encontre no painel WhatsApp Business
   - Formato: 123456789012345

## 🔐 Configuração de Segurança

### 1. Variáveis de Ambiente

Crie/atualize o arquivo `.env`:

```env
# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=seu_token_de_acesso_permanente
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_VERIFY_TOKEN=whatsapp_verify_token_123
WHATSAPP_APP_SECRET=seu_app_secret

# Meta App
META_APP_ID=seu_app_id
META_APP_SECRET=seu_app_secret

# Webhook
WEBHOOK_VERIFY_TOKEN=whatsapp_verify_token_123
```

### 2. Validação de Webhook

Atualize `backend/core/views/webhook_views.py`:

```python
import hmac
import hashlib
from django.conf import settings

def verify_webhook_signature(request):
    """Verifica assinatura do webhook do WhatsApp"""
    signature = request.headers.get('X-Hub-Signature-256', '')
    if not signature:
        return False
    
    expected_signature = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode('utf-8'),
        request.body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f'sha256={expected_signature}', signature)
```

## 📱 Configuração do Número

### 1. Adicionar Número de Telefone

1. **No painel WhatsApp Business**
   - Clique em "Adicionar número de telefone"
   - Insira seu número comercial
   - Verifique via SMS/chamada

2. **Configurar Nome de Exibição**
   - Nome da empresa: "Sua Empresa"
   - Categoria: Selecione apropriada
   - Descrição: Breve descrição do negócio

### 2. Configurar Templates de Mensagem

```json
{
  "name": "welcome_message",
  "category": "UTILITY",
  "language": "pt_BR",
  "components": [
    {
      "type": "BODY",
      "text": "Olá {{1}}! Bem-vindo à nossa empresa. Como podemos ajudá-lo hoje?"
    }
  ]
}
```

## 🧪 Testes de Produção

### 1. Teste de Webhook

```bash
# Teste manual
curl -X POST "https://seu-dominio.com/api/webhook/" \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=sua_assinatura" \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [{
      "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
      "changes": [{
        "value": {
          "messaging_product": "whatsapp",
          "metadata": {
            "display_phone_number": "15550559999",
            "phone_number_id": "PHONE_NUMBER_ID"
          },
          "messages": [{
            "from": "5511999999999",
            "id": "wamid.ID",
            "timestamp": "1234567890",
            "text": {
              "body": "Olá, teste de produção!"
            },
            "type": "text"
          }]
        },
        "field": "messages"
      }]
    }]
  }'
```

### 2. Teste de Envio

```python
# Script de teste
import requests
import os

def test_send_message():
    url = f"https://graph.facebook.com/v18.0/{os.getenv('WHATSAPP_PHONE_NUMBER_ID')}/messages"
    
    headers = {
        'Authorization': f"Bearer {os.getenv('WHATSAPP_ACCESS_TOKEN')}",
        'Content-Type': 'application/json'
    }
    
    data = {
        'messaging_product': 'whatsapp',
        'to': '5511999999999',  # Seu número de teste
        'type': 'text',
        'text': {
            'body': 'Teste de envio via API de produção!'
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    test_send_message()
```

## 🚀 Deploy em Produção

### 1. Configuração do Servidor

```bash
# Instalar dependências
pip install gunicorn nginx-python

# Configurar Gunicorn
gunicorn --bind 0.0.0.0:8000 config.wsgi:application

# Configurar Nginx
sudo nano /etc/nginx/sites-available/whatsapp-automation
```

### 2. Configuração SSL

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obter certificado SSL
sudo certbot --nginx -d seu-dominio.com
```

### 3. Configuração de Domínio

```nginx
server {
    listen 80;
    server_name seu-dominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name seu-dominio.com;
    
    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 Monitoramento

### 1. Logs de Webhook

```python
# Adicionar ao webhook_views.py
import logging

logger = logging.getLogger(__name__)

def whatsapp_webhook(request):
    logger.info(f"Webhook recebido: {request.body}")
    # ... resto do código
```

### 2. Métricas

```python
# Adicionar métricas
from django.core.cache import cache

def track_message_metrics(message_type, status):
    key = f"whatsapp_metrics_{message_type}_{status}"
    cache.set(key, cache.get(key, 0) + 1, timeout=86400)
```

## 🔍 Troubleshooting

### Problemas Comuns

1. **Webhook não recebe mensagens**
   - Verificar URL do webhook
   - Confirmar token de verificação
   - Checar logs do servidor

2. **Erro de autenticação**
   - Verificar token de acesso
   - Confirmar Phone Number ID
   - Checar permissões do app

3. **Mensagens não são enviadas**
   - Verificar formato do número
   - Confirmar template aprovado
   - Checar limites de rate

### Comandos Úteis

```bash
# Verificar status do webhook
curl -X GET "https://graph.facebook.com/v18.0/PHONE_NUMBER_ID" \
  -H "Authorization: Bearer ACCESS_TOKEN"

# Listar templates
curl -X GET "https://graph.facebook.com/v18.0/WHATSAPP_BUSINESS_ACCOUNT_ID/message_templates" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

## 📚 Recursos Adicionais

- [Documentação Oficial](https://developers.facebook.com/docs/whatsapp)
- [API Reference](https://developers.facebook.com/docs/whatsapp/cloud-api/reference)
- [Webhook Guide](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks)
- [Templates Guide](https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates)

---

**⚠️ Importante:** Mantenha seus tokens seguros e nunca os compartilhe publicamente!