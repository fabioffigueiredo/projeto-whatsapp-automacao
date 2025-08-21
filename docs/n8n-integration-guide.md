# Guia de Integração n8n - WhatsApp Automation

## 📋 Visão Geral

Este guia explica como integrar e usar o n8n com o sistema de automação do WhatsApp para criar workflows avançados, analytics e automações inteligentes.

## 🚀 Configuração Inicial

### 1. Configuração do Docker

O n8n já está configurado no `docker-compose.yml`. Para iniciar:

```bash
# Copie o arquivo de ambiente
cp .env.example .env

# Configure as variáveis do n8n no .env
N8N_USER=admin
N8N_PASSWORD=sua-senha-segura
N8N_WEBHOOK_URL=http://localhost:5678

# Inicie os serviços
docker-compose up -d
```

### 2. Acesso ao n8n

- **URL**: http://localhost:5678
- **Usuário**: admin (ou conforme configurado)
- **Senha**: conforme configurado no .env

## 🔧 Workflows Disponíveis

### 1. Workflow Básico (`workflow.json`)

**Funcionalidade**: Orquestração simples de mensagens WhatsApp

**Fluxo**:
1. Recebe webhook do WhatsApp
2. Extrai dados da mensagem
3. Chama API Django
4. Retorna resposta

### 2. Workflow Avançado (`advanced-workflow.json`)

**Funcionalidades**:
- ✅ Validação avançada de entrada
- 📊 Analytics automático
- 💳 Processamento de pagamentos
- 📱 Notificações inteligentes
- 🔍 Monitoramento de estados

**Fluxo Detalhado**:
1. **Recepção**: Webhook WhatsApp
2. **Validação**: Extração e validação de dados
3. **Processamento**: Chamada para API Django
4. **Analytics**: Log automático de métricas
5. **Condicionais**: Verificação de estado de pagamento
6. **Ações**: Processamento de pagamento e notificações

## 📡 Endpoints da API Django

### Analytics
```http
POST /api/n8n/analytics/
Content-Type: application/json

{
  "phone": "5511999999999",
  "message": "Olá",
  "conversationState": "NODE_1_GREETING",
  "responseTime": 150,
  "success": true,
  "timestamp": "2024-01-01T10:00:00Z"
}
```

### Notificações
```http
POST /api/n8n/notifications/
Content-Type: application/json

{
  "phone": "5511999999999",
  "type": "payment_initiated",
  "data": {
    "amount": 100.00,
    "payment_id": "pay_123"
  }
}
```

### Pagamentos
```http
POST /api/n8n/payments/
Content-Type: application/json

{
  "phone": "5511999999999",
  "amount": 100.00
}
```

### Webhook Genérico
```http
POST /api/n8n/webhook/
Content-Type: application/json

{
  "type": "payment_status",
  "payment_id": "pay_123",
  "status": "completed",
  "phone": "5511999999999"
}
```

## 🔄 Configuração de Workflows

### Importando Workflows

1. Acesse o n8n (http://localhost:5678)
2. Clique em "Import from file"
3. Selecione o arquivo de workflow:
   - `n8n/workflow.json` (básico)
   - `n8n/advanced-workflow.json` (avançado)
4. Configure as credenciais se necessário
5. Ative o workflow

### Configuração de Webhooks

**URL do Webhook n8n**: `http://localhost:5678/webhook/whatsapp-webhook`

**Configuração no WhatsApp Business API**:
```bash
# Configure o webhook para apontar para o n8n
WHATSAPP_WEBHOOK_URL=http://localhost:5678/webhook/whatsapp-webhook
```

## 📊 Funcionalidades Avançadas

### 1. Analytics Automático

- **Métricas coletadas**:
  - Tempo de resposta
  - Estados de conversação
  - Taxa de sucesso
  - Volume de mensagens

- **Visualização**: Dados enviados para endpoint de analytics

### 2. Processamento de Pagamentos

- **Detecção automática**: Identifica quando usuário está no estado de pagamento
- **Processamento**: Cria link de pagamento automaticamente
- **Notificações**: Envia confirmações via WhatsApp

### 3. Notificações Inteligentes

**Tipos de notificação**:
- `payment_initiated`: Pagamento iniciado
- `payment_completed`: Pagamento concluído
- `payment_failed`: Erro no pagamento
- `system_alert`: Alertas do sistema

### 4. Monitoramento de Sistema

- **Health checks**: Verificação automática de saúde
- **Alertas**: Notificações de problemas
- **Logs**: Registro detalhado de atividades

## 🛠️ Customização

### Criando Novos Workflows

1. **Planejamento**: Defina o fluxo desejado
2. **Criação**: Use a interface visual do n8n
3. **Integração**: Configure chamadas para APIs Django
4. **Teste**: Valide o funcionamento
5. **Deploy**: Ative o workflow

### Adicionando Novos Endpoints

1. **Backend**: Crie novos endpoints em `n8n_integration.py`
2. **URLs**: Adicione rotas em `urls/__init__.py`
3. **n8n**: Configure nós HTTP Request
4. **Teste**: Valide a integração

## 🔍 Monitoramento e Debug

### Logs do n8n

```bash
# Visualizar logs do n8n
docker logs whatsapp_n8n -f
```

### Logs do Django

```bash
# Logs da aplicação
tail -f backend/logs/django.log

# Logs específicos do n8n
grep "N8N" backend/logs/django.log
```

### Debug de Workflows

1. **Execuções**: Visualize execuções no painel do n8n
2. **Dados**: Inspecione dados entre nós
3. **Erros**: Analise mensagens de erro
4. **Teste**: Use modo de teste para validar

## 📈 Casos de Uso Avançados

### 1. Campanhas de Marketing

```javascript
// Exemplo de nó Function para campanhas
const campaigns = {
  'new_user': 'Bem-vindo! Aproveite 10% de desconto',
  'inactive_user': 'Sentimos sua falta! Volte e ganhe bônus',
  'high_value': 'Oferta VIP especial para você'
};

const userType = $json.user_type;
const message = campaigns[userType] || campaigns['new_user'];

return [{ message, phone: $json.phone }];
```

### 2. Análise de Sentimento

```javascript
// Análise básica de sentimento
const message = $json.message.toLowerCase();
const positiveWords = ['obrigado', 'ótimo', 'excelente', 'perfeito'];
const negativeWords = ['problema', 'erro', 'ruim', 'péssimo'];

let sentiment = 'neutral';
if (positiveWords.some(word => message.includes(word))) {
  sentiment = 'positive';
} else if (negativeWords.some(word => message.includes(word))) {
  sentiment = 'negative';
}

return [{ ....$json, sentiment }];
```

### 3. Escalação Automática

```javascript
// Escalação para atendimento humano
const escalationTriggers = [
  'falar com atendente',
  'problema urgente',
  'reclamação',
  'cancelar'
];

const message = $json.message.toLowerCase();
const needsEscalation = escalationTriggers.some(trigger => 
  message.includes(trigger)
);

if (needsEscalation) {
  return [{
    action: 'escalate',
    phone: $json.phone,
    reason: 'User requested human assistance'
  }];
}

return [{ action: 'continue', ...$json }];
```

## 🚀 Próximos Passos

1. **Implemente workflows básicos**
2. **Configure analytics**
3. **Teste funcionalidades avançadas**
4. **Customize conforme necessário**
5. **Monitore performance**
6. **Expanda funcionalidades**

## 📞 Suporte

Para dúvidas sobre a integração:
1. Consulte logs do sistema
2. Verifique configurações de rede
3. Teste endpoints individualmente
4. Analise execuções no n8n

---

**Nota**: Este guia assume conhecimento básico do n8n e Docker. Para mais informações, consulte a [documentação oficial do n8n](https://docs.n8n.io/).