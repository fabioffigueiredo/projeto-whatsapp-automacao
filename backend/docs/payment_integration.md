# Sistema de Pagamentos Integrado

Este documento descreve o sistema de pagamentos integrado implementado no projeto de automação WhatsApp para transferências de dinheiro.

## Visão Geral

O sistema suporta múltiplos provedores de pagamento através de uma arquitetura modular:

- **Stripe**: Para pagamentos internacionais
- **MercadoPago**: Para pagamentos na América Latina
- **Extensível**: Fácil adição de novos provedores

## Configuração

### Variáveis de Ambiente

Adicione as seguintes configurações no arquivo `config/settings.py`:

```python
# Configurações de Pagamento
PAYMENT_PROVIDER = os.getenv('PAYMENT_PROVIDER', 'stripe')  # 'stripe' ou 'mercadopago'
PAYMENT_API_KEY = os.getenv('PAYMENT_API_KEY')
PAYMENT_SECRET_KEY = os.getenv('PAYMENT_SECRET_KEY')
PAYMENT_WEBHOOK_SECRET = os.getenv('PAYMENT_WEBHOOK_SECRET')
PAYMENT_WEBHOOK_URL = os.getenv('PAYMENT_WEBHOOK_URL', 'https://yourdomain.com/api/webhooks/payment/')
PAYMENT_SUCCESS_URL = os.getenv('PAYMENT_SUCCESS_URL', 'https://yourdomain.com/payment/success/')
PAYMENT_CANCEL_URL = os.getenv('PAYMENT_CANCEL_URL', 'https://yourdomain.com/payment/cancel/')
```

### Configuração do Stripe

1. Crie uma conta no [Stripe](https://stripe.com)
2. Obtenha suas chaves API (Publishable Key e Secret Key)
3. Configure o webhook endpoint para receber notificações
4. Defina as variáveis de ambiente:

```bash
PAYMENT_PROVIDER=stripe
PAYMENT_API_KEY=pk_test_...
PAYMENT_SECRET_KEY=sk_test_...
PAYMENT_WEBHOOK_SECRET=whsec_...
```

### Configuração do MercadoPago

1. Crie uma conta no [MercadoPago Developers](https://developers.mercadopago.com)
2. Obtenha seu Access Token
3. Configure o webhook endpoint
4. Defina as variáveis de ambiente:

```bash
PAYMENT_PROVIDER=mercadopago
PAYMENT_API_KEY=APP_USR_...
PAYMENT_SECRET_KEY=APP_USR_...
PAYMENT_WEBHOOK_SECRET=your_webhook_secret
```

## Fluxo de Pagamento

### 1. Criação da Transferência

```python
# O cliente cria uma transferência através do WhatsApp ou API
transfer = transfer_service.create_transfer(client, transfer_data)
```

### 2. Geração do Link de Pagamento

```python
# Gera link de pagamento usando o provedor configurado
payment_link = transfer_service.generate_payment_link(transfer)
```

### 3. Processamento do Pagamento

- Cliente acessa o link e realiza o pagamento
- Provedor processa o pagamento
- Webhook é enviado para nossa aplicação

### 4. Confirmação via Webhook

```python
# Webhook recebe notificação do provedor
# Status da transferência é atualizado automaticamente
# Cliente é notificado via WhatsApp
```

## Endpoints da API

### Gerar Link de Pagamento

```http
POST /api/transfers/{transfer_id}/payment-link/
Authorization: Bearer {jwt_token}
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "payment_link": "https://checkout.stripe.com/pay/cs_...",
    "transfer_id": "TXN123456",
    "total_amount_usd": 100.00
  },
  "message": "Link de pagamento gerado com sucesso"
}
```

### Verificar Status do Pagamento

```http
GET /api/transfers/{transfer_id}/payment-status/
Authorization: Bearer {jwt_token}
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "transfer_status": "payment_confirmed",
    "payment_status": "completed",
    "payment_amount": 100.00,
    "payment_currency": "USD",
    "last_updated": "2024-01-15T10:30:00Z"
  }
}
```

### Webhook de Pagamento

```http
POST /api/webhooks/payment/
Content-Type: application/json
```

**Payload:**
```json
{
  "ref": "payment_reference_id",
  "status": "paid"
}
```

## Status de Transferência

O sistema utiliza os seguintes status para transferências:

- `draft`: Transferência criada, aguardando dados
- `pending_payment`: Aguardando pagamento do cliente
- `payment_confirmed`: Pagamento confirmado
- `processing`: Transferência sendo processada
- `completed`: Transferência concluída
- `failed`: Transferência falhou
- `cancelled`: Transferência cancelada

## Segurança

### Verificação de Webhook

Todos os webhooks são verificados usando HMAC SHA-256:

```python
def verify_webhook_signature(request):
    signature = request.headers.get('X-Signature')
    payload = request.body
    expected_signature = hmac.new(
        settings.PAYMENT_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)
```

### Logs de Auditoria

Todos os webhooks são registrados na tabela `WebhookLog` para auditoria:

```python
WebhookLog.objects.create(
    source="payment",
    payload=request.data,
    status="received"
)
```

## Tratamento de Erros

### Pagamento Falhou

- Status da transferência é atualizado para `failed`
- Cliente é notificado via WhatsApp
- Possibilidade de tentar novamente

### Webhook Perdido

- Sistema permite verificação manual do status
- Endpoint `/payment-status/` consulta diretamente o provedor
- Atualização automática do status se necessário

### Timeout de Pagamento

- Links de pagamento têm validade configurável
- Status automaticamente atualizado após expiração
- Cliente pode gerar novo link se necessário

## Monitoramento

### Logs

Todos os eventos importantes são registrados:

```python
logger.info(f"Payment link generated for transfer {transfer.id}")
logger.info(f"Payment confirmed for transfer {transfer.id}")
logger.error(f"Payment failed for transfer {transfer.id}: {error}")
```

### Métricas Recomendadas

- Taxa de conversão de pagamentos
- Tempo médio de processamento
- Taxa de falhas por provedor
- Volume de transações por período

## Desenvolvimento e Testes

### Modo de Desenvolvimento

Quando `PAYMENT_API_KEY` não está configurado, o sistema opera em modo simulado:

```python
if not getattr(settings, 'PAYMENT_API_KEY', None):
    # Retorna dados simulados para desenvolvimento
    return {
        'success': True,
        'payment_url': 'https://example.com/mock-payment',
        'payment_id': 'mock_payment_123'
    }
```

### Testes de Webhook

Para testar webhooks localmente, use ferramentas como ngrok:

```bash
ngrok http 8000
# Configure o webhook URL no provedor para: https://abc123.ngrok.io/api/webhooks/payment/
```

## Extensibilidade

### Adicionando Novo Provedor

1. Crie uma nova classe herdando de `PaymentProvider`:

```python
class NovoProvedorProvider(PaymentProvider):
    def create_payment_link(self, payment_data: Dict) -> Dict:
        # Implementar integração
        pass
    
    def verify_payment(self, payment_id: str) -> Dict:
        # Implementar verificação
        pass
```

2. Adicione ao factory em `get_payment_provider()`:

```python
def get_payment_provider() -> PaymentProvider:
    provider_name = getattr(settings, 'PAYMENT_PROVIDER', 'stripe')
    
    if provider_name == 'novo_provedor':
        return NovoProvedorProvider()
    # ...
```

3. Configure as variáveis de ambiente necessárias

## Troubleshooting

### Problemas Comuns

1. **Webhook não recebido**
   - Verificar URL do webhook no provedor
   - Verificar conectividade de rede
   - Verificar logs do servidor

2. **Assinatura inválida**
   - Verificar `PAYMENT_WEBHOOK_SECRET`
   - Verificar formato da assinatura
   - Verificar encoding do payload

3. **Pagamento não confirmado**
   - Usar endpoint `/payment-status/` para verificar
   - Verificar logs do provedor
   - Verificar configuração das chaves API

### Logs Úteis

```bash
# Verificar logs de pagamento
grep "payment" logs/django.log

# Verificar webhooks recebidos
grep "webhook" logs/django.log

# Verificar erros de integração
grep "ERROR.*payment" logs/django.log
```