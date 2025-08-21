# 🚀 Guia Manual de Configuração do n8n

Este guia te ajudará a configurar o n8n manualmente para integração com o sistema WhatsApp.

## 📋 Pré-requisitos

- Docker e Docker Compose instalados
- Projeto WhatsApp rodando
- Acesso ao terminal

## 🔧 Passo 1: Iniciar os Serviços

```bash
# No diretório do projeto
docker-compose up -d
```

Verifique se todos os serviços estão rodando:
```bash
docker-compose ps
```

Você deve ver:
- ✅ `backend` (Django)
- ✅ `db` (PostgreSQL) 
- ✅ `redis`
- ✅ `n8n`

## 🌐 Passo 2: Acessar o n8n

1. Abra seu navegador
2. Acesse: http://localhost:5678
3. **Primeira vez**: Configure sua conta admin
   - Email: `admin@example.com`
   - Password: `admin123`
   - First Name: `Admin`
   - Last Name: `User`

## 📥 Passo 3: Importar Workflows

### Workflow Básico

1. No n8n, clique em **"+ Add workflow"**
2. Clique no menu **"..."** → **"Import from file"**
3. Selecione o arquivo: `n8n/workflow.json`
4. Clique **"Save"** e depois **"Activate"**

### Workflow Avançado

1. Repita o processo acima
2. Selecione o arquivo: `n8n/advanced-workflow.json`
3. **Save** e **Activate**

## ⚙️ Passo 4: Configurar Webhooks

### No n8n:

1. Abra o workflow **"WhatsApp Orchestrator"**
2. Clique no nó **"Webhook In"**
3. Copie a URL do webhook (algo como: `http://localhost:5678/webhook/abc123`)

### No WhatsApp Business API:

1. Configure o webhook URL para apontar para o n8n
2. Use a URL copiada acima
3. Configure o verify token conforme necessário

## 🔗 Passo 5: Configurar Conexões

### Conexão com Django

1. No workflow, clique no nó **"Call Django API"**
2. Verifique se a URL está: `http://backend:8000/api/webhook/whatsapp`
3. Método: `POST`
4. Headers: `Content-Type: application/json`

### Conexão com Banco de Dados (Opcional)

1. Vá em **Settings** → **Credentials**
2. Adicione nova credencial **"Postgres"**
3. Configure:
   - Host: `db`
   - Port: `5432`
   - Database: `whatsapp_db`
   - User: `postgres`
   - Password: `postgres`

## 🧪 Passo 6: Testar a Integração

### Teste Manual no n8n

1. Abra o workflow
2. Clique em **"Execute Workflow"**
3. No nó Webhook, clique **"Listen for calls"**
4. Envie uma requisição de teste:

```bash
curl -X POST http://localhost:5678/webhook/SEU_WEBHOOK_ID \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5511999999999",
    "message": "Teste de integração"
  }'
```

### Teste com Script Python

```bash
python test_n8n_integration.py
```

## 📊 Passo 7: Configurar Analytics (Opcional)

1. No workflow avançado, configure o nó **"Analytics Logger"**
2. URL: `http://backend:8000/api/n8n/analytics/`
3. Método: `POST`

## 🔔 Passo 8: Configurar Notificações

1. Configure o nó **"Send Notification"**
2. URL: `http://backend:8000/api/n8n/notifications/`
3. Adicione lógica para diferentes tipos de notificação

## 🚨 Solução de Problemas

### n8n não carrega
```bash
# Verificar logs
docker-compose logs n8n

# Reiniciar serviço
docker-compose restart n8n
```

### Erro de conexão com Django
```bash
# Verificar se Django está rodando
curl http://localhost:8000/api/

# Verificar logs do Django
docker-compose logs backend
```

### Webhook não funciona
1. Verifique se o workflow está **ativo**
2. Confirme a URL do webhook
3. Teste com curl primeiro
4. Verifique logs do n8n

### Problemas de autenticação
1. Limpe cookies do navegador
2. Acesse http://localhost:5678 em aba anônima
3. Reconfigure a conta se necessário

## 📈 Monitoramento

### Logs em Tempo Real
```bash
# Todos os serviços
docker-compose logs -f

# Apenas n8n
docker-compose logs -f n8n

# Apenas Django
docker-compose logs -f backend
```

### Verificar Status
```bash
# Status dos containers
docker-compose ps

# Uso de recursos
docker stats
```

## 🔧 Configurações Avançadas

### Variáveis de Ambiente

Edite o arquivo `.env`:

```env
# n8n
N8N_USER=admin@example.com
N8N_PASSWORD=admin123
N8N_WEBHOOK_URL=http://localhost:5678/webhook

# Django
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True

# WhatsApp
WHATSAPP_TOKEN=your-token
WHATSAPP_VERIFY_TOKEN=your-verify-token
```

### Backup de Workflows

1. No n8n, vá em **Settings** → **Import/Export**
2. Exporte todos os workflows
3. Salve o arquivo JSON como backup

### Escalabilidade

Para produção, considere:

1. **Banco de dados externo** para n8n
2. **Load balancer** para múltiplas instâncias
3. **Monitoramento** com Prometheus/Grafana
4. **Backup automático** dos workflows

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs: `docker-compose logs`
2. Teste cada componente individualmente
3. Consulte a documentação do n8n: https://docs.n8n.io
4. Execute o script de teste: `python test_n8n_integration.py`

## 🎯 Próximos Passos

Após a configuração:

1. ✅ Teste com mensagens reais do WhatsApp
2. ✅ Configure analytics e monitoramento
3. ✅ Implemente workflows personalizados
4. ✅ Configure backup automático
5. ✅ Documente processos específicos do seu negócio

---

**🚀 Parabéns! Seu n8n está configurado e pronto para uso!**