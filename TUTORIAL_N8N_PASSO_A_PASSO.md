# 📋 Tutorial N8N - Passo a Passo

## 🎯 Objetivo
Configurar o N8N para automatizar o processamento de mensagens WhatsApp no seu projeto.

## 📝 Pré-requisitos
- ✅ Docker rodando
- ✅ Projeto WhatsApp funcionando
- ✅ N8N acessível em http://localhost:5678

## 🚀 Passo 1: Acessar o N8N

1. **Abra seu navegador**
2. **Digite:** `http://localhost:5678`
3. **Aguarde carregar** a interface do N8N

### Primeira Vez?
Se for a primeira vez:
1. Clique em **"Get Started"**
2. Preencha:
   - **Email:** `admin@localhost`
   - **First Name:** `Admin`
   - **Last Name:** `User`
   - **Password:** `admin123` (ou sua preferência)
3. Clique **"Next"**
4. Pule as configurações opcionais

## 🔧 Passo 2: Importar Workflow Básico

### 2.1 Acessar Importação
1. Na tela principal, clique no **menu hambúrguer** (☰) no canto superior esquerdo
2. Clique em **"Import from file"**

### 2.2 Selecionar Arquivo
1. Clique em **"Select file"**
2. Navegue até: `C:\Users\Fabio\Desktop\projetos\projeto-whatsapp-automacao\n8n\workflow.json`
3. Selecione o arquivo
4. Clique **"Import"**

### 2.3 Verificar Importação
Você verá o workflow **"WhatsApp Orchestrator (Django API)"** com 4 nodes:
- 🔗 **Webhook In** (entrada)
- ⚙️ **Extract** (processamento)
- 🌐 **Call Django API** (envio)
- 📤 **Respond** (resposta)

## ⚡ Passo 3: Ativar o Workflow

1. **Clique no botão "Inactive"** no canto superior direito
2. Ele mudará para **"Active"** (verde)
3. O workflow agora está **rodando**!

## 🔗 Passo 4: Obter URL do Webhook

1. **Clique duas vezes** no node **"Webhook In"**
2. Na janela que abrir, você verá:
   - **Webhook URL:** `http://localhost:5678/webhook/whatsapp-hook`
3. **Copie esta URL** - você usará para configurar o WhatsApp

## 🧪 Passo 5: Testar o Workflow

### 5.1 Teste Manual
1. Abra um novo terminal
2. Execute este comando para simular uma mensagem:

```bash
curl -X POST http://localhost:5678/webhook/whatsapp-hook \
  -H "Content-Type: application/json" \
  -d '{"phone": "5511999999999", "message": "oi"}'
```

### 5.2 Verificar Resultado
1. No N8N, clique em **"Executions"** no menu lateral
2. Você verá a execução do teste
3. Clique nela para ver detalhes
4. Verifique se todos os nodes executaram com sucesso (✅)

## 🔄 Passo 6: Importar Workflow Avançado (Opcional)

### 6.1 Importar
1. Repita o processo de importação
2. Desta vez selecione: `advanced-workflow.json`
3. Importe o workflow **"WhatsApp Advanced Orchestrator"**

### 6.2 Recursos do Workflow Avançado
- ✅ Validação mais robusta
- ✅ Tratamento de erros
- ✅ Logs detalhados
- ✅ Suporte a diferentes tipos de mensagem
- ✅ Retry automático

## 🛠️ Passo 7: Configurações Importantes

### 7.1 Verificar URL do Backend
1. No workflow, clique duas vezes no node **"Call Django API"**
2. Verifique se a URL está: `http://backend:8000/api/webhook/whatsapp`
3. Se estiver diferente, corrija para esta URL

### 7.2 Configurar Headers (se necessário)
Se o Django exigir autenticação:
1. No node **"Call Django API"**
2. Vá em **"Headers"**
3. Adicione:
   - **Name:** `Authorization`
   - **Value:** `Bearer SEU_TOKEN`

## 📊 Passo 8: Monitoramento

### 8.1 Ver Execuções
1. Clique em **"Executions"** no menu
2. Veja todas as execuções dos workflows
3. Verde = Sucesso, Vermelho = Erro

### 8.2 Debug de Erros
1. Clique em uma execução com erro
2. Veja qual node falhou
3. Clique no node para ver detalhes do erro
4. Corrija o problema e teste novamente

## 🔧 Passo 9: Personalização

### 9.1 Modificar Processamento
Para alterar como as mensagens são processadas:
1. Clique duas vezes no node **"Extract"**
2. Modifique o código JavaScript
3. Exemplo - adicionar timestamp:

```javascript
const b = $json.body || $json;
return [{ 
  phone: b.phone || b.From || '', 
  message: b.message || b.Body || '',
  timestamp: new Date().toISOString()
}];
```

### 9.2 Adicionar Novos Nodes
1. Arraste nodes da barra lateral
2. Conecte com os existentes
3. Configure conforme necessário

## 🚨 Troubleshooting

### Problema: Workflow não ativa
**Solução:**
1. Verifique se todos os nodes estão configurados
2. Clique em cada node e veja se há erros (❌)
3. Corrija configurações e tente novamente

### Problema: Erro 404 no Django
**Solução:**
1. Verifique se o Django está rodando: `docker-compose ps`
2. Verifique se a URL está correta: `http://backend:8000/api/webhook/whatsapp`
3. Teste a URL manualmente

### Problema: Webhook não recebe dados
**Solução:**
1. Verifique se o workflow está **Active**
2. Teste com curl (comando do Passo 5.1)
3. Verifique logs: `docker-compose logs n8n`

## 📱 Passo 10: Integração com WhatsApp Real

### 10.1 Configurar Webhook no WhatsApp Business API
1. Use a URL: `http://SEU_DOMINIO:5678/webhook/whatsapp-hook`
2. Configure o método: **POST**
3. Adicione headers se necessário

### 10.2 Ngrok para Testes Locais
Para testar localmente com WhatsApp real:

```bash
# Instalar ngrok
npm install -g ngrok

# Expor porta 5678
ngrok http 5678

# Use a URL gerada no WhatsApp Business API
```

## ✅ Checklist Final

- [ ] N8N acessível em http://localhost:5678
- [ ] Workflow importado e ativo
- [ ] Teste manual funcionando
- [ ] Django recebendo dados
- [ ] Monitoramento configurado
- [ ] Webhook URL copiada

## 🎉 Próximos Passos

1. **Configure o WhatsApp Business API** com a URL do webhook
2. **Teste com mensagens reais**
3. **Monitore execuções** regularmente
4. **Customize workflows** conforme necessário
5. **Implemente novos fluxos** (pagamentos, notificações, etc.)

---

**🚀 Parabéns! Seu N8N está configurado e funcionando!**

Agora você pode processar mensagens WhatsApp automaticamente através do N8N → Django → Banco de Dados.

**URLs Importantes:**
- **N8N:** http://localhost:5678
- **Webhook:** http://localhost:5678/webhook/whatsapp-hook
- **Django:** http://localhost:8000