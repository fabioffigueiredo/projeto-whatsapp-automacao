# 🚀 Guia Completo do N8N para Automação WhatsApp

## 📋 O que é o N8N?

O N8N é uma ferramenta de automação de workflows que permite conectar diferentes serviços e APIs de forma visual, sem precisar escrever código complexo. No seu projeto, ele será usado para:

- ✅ Processar mensagens do WhatsApp
- ✅ Integrar com APIs de pagamento
- ✅ Automatizar fluxos de transferência
- ✅ Gerenciar webhooks e notificações

## 🌐 Acessando o N8N

**URL de Acesso:** http://localhost:5678

1. Abra seu navegador
2. Digite: `http://localhost:5678`
3. Você verá a interface do N8N

## 🎯 Primeiros Passos

### 1. Configuração Inicial

Quando acessar pela primeira vez:

1. **Criar Conta:** O N8N pedirá para criar uma conta local
2. **Email:** Use qualquer email (ex: admin@localhost)
3. **Senha:** Crie uma senha segura
4. **Nome:** Seu nome ou "Admin"

### 2. Interface Principal

A interface do N8N tem:

- **📊 Dashboard:** Visão geral dos workflows
- **⚡ Workflows:** Lista de automações criadas
- **🔧 Credentials:** Configurações de APIs e tokens
- **📈 Executions:** Histórico de execuções

## 🛠️ Criando seu Primeiro Workflow

### Passo 1: Novo Workflow

1. Clique em **"New Workflow"**
2. Você verá um canvas em branco
3. No lado esquerdo há uma lista de "nodes" (blocos)

### Passo 2: Adicionando Nodes

**Nodes Essenciais para WhatsApp:**

1. **Webhook** - Recebe dados do WhatsApp
2. **HTTP Request** - Faz chamadas para APIs
3. **Code** - Executa JavaScript personalizado
4. **IF** - Condições lógicas
5. **Set** - Define variáveis

### Passo 3: Configurando Webhook

1. Arraste o node **"Webhook"** para o canvas
2. Clique duas vezes nele
3. Configure:
   - **HTTP Method:** POST
   - **Path:** `/webhook/whatsapp`
   - **Response Mode:** Respond to Webhook

## 🔗 Integrando com seu Projeto WhatsApp

### Workflow Básico para WhatsApp

```
[Webhook] → [Code] → [HTTP Request] → [Response]
```

### 1. Node Webhook (Entrada)

**Configuração:**
```
HTTP Method: POST
Path: /webhook/whatsapp
Response Mode: Respond to Webhook
```

### 2. Node Code (Processamento)

**JavaScript para processar mensagem:**
```javascript
// Extrair dados da mensagem WhatsApp
const message = $json.message;
const phone = $json.phone;
const timestamp = $json.timestamp;

// Processar mensagem
const processedData = {
  phone: phone,
  message: message.toLowerCase().trim(),
  timestamp: timestamp,
  type: 'whatsapp_message'
};

return { json: processedData };
```

### 3. Node HTTP Request (Envio para Django)

**Configuração:**
```
Method: POST
URL: http://backend:8000/api/webhook/process/
Headers:
  Content-Type: application/json
Body: {{ $json }}
```

### 4. Node Response (Resposta)

**Configuração:**
```
Response Code: 200
Response Body: {{ $json }}
```

## 📱 Workflows Específicos do Projeto

### Workflow 1: Processamento de Mensagens

**Objetivo:** Receber e processar mensagens do WhatsApp

**Fluxo:**
1. Webhook recebe mensagem
2. Code processa e valida dados
3. HTTP Request envia para Django
4. Response confirma recebimento

### Workflow 2: Notificações de Pagamento

**Objetivo:** Processar webhooks de pagamento

**Fluxo:**
1. Webhook recebe notificação de pagamento
2. Code valida dados do pagamento
3. IF verifica se pagamento foi aprovado
4. HTTP Request atualiza status no Django
5. HTTP Request envia confirmação via WhatsApp

### Workflow 3: Monitoramento de Sistema

**Objetivo:** Monitorar saúde do sistema

**Fluxo:**
1. Cron trigger (executa a cada 5 minutos)
2. HTTP Request verifica status do Django
3. IF verifica se sistema está saudável
4. Se não estiver, envia alerta

## 🔧 Configurações Avançadas

### Credentials (Credenciais)

Para APIs externas, configure credenciais:

1. Vá em **Settings → Credentials**
2. Clique **"Create New"**
3. Escolha o tipo (ex: HTTP Header Auth)
4. Configure tokens/chaves

### Environment Variables

Use variáveis de ambiente para:
- URLs de APIs
- Tokens secretos
- Configurações por ambiente

### Error Handling

Configure tratamento de erros:
1. Use node **"Error Trigger"**
2. Configure retry automático
3. Envie notificações de erro

## 📊 Monitoramento e Debug

### Executions (Execuções)

1. Vá em **Executions**
2. Veja histórico de execuções
3. Clique em execução para ver detalhes
4. Debug erros e problemas

### Logs

Para ver logs detalhados:
```bash
docker-compose logs n8n
```

## 🚀 Workflows Prontos para Importar

Seu projeto já tem workflows prontos:

### 1. Workflow Básico
**Arquivo:** `n8n/workflow.json`

**Como importar:**
1. No N8N, clique **"Import from File"**
2. Selecione `n8n/workflow.json`
3. Clique **"Import"**

### 2. Workflow Avançado
**Arquivo:** `n8n/advanced-workflow.json`

**Recursos:**
- Processamento completo de mensagens
- Integração com pagamentos
- Tratamento de erros
- Monitoramento

## 🔗 URLs Importantes

- **N8N Interface:** http://localhost:5678
- **Django Backend:** http://localhost:8000
- **Webhook N8N:** http://localhost:5678/webhook/whatsapp
- **API Django:** http://localhost:8000/api/

## 🆘 Troubleshooting

### Problema: N8N não abre
**Solução:**
```bash
docker-compose restart n8n
```

### Problema: Webhook não funciona
**Verificar:**
1. URL está correta
2. Method é POST
3. Headers estão configurados
4. Firewall não está bloqueando

### Problema: Erro de conexão com Django
**Verificar:**
1. Django está rodando
2. URL é `http://backend:8000` (dentro do Docker)
3. Endpoints existem

## 📚 Próximos Passos

1. **Acesse o N8N:** http://localhost:5678
2. **Crie sua conta**
3. **Importe o workflow básico**
4. **Teste com uma mensagem**
5. **Customize conforme necessário**

## 💡 Dicas Importantes

- ✅ Sempre teste workflows antes de usar em produção
- ✅ Use credentials para dados sensíveis
- ✅ Configure error handling
- ✅ Monitore execuções regularmente
- ✅ Faça backup dos workflows

---

**🎉 Agora você está pronto para usar o N8N!**

Comece acessando http://localhost:5678 e criando sua primeira automação!