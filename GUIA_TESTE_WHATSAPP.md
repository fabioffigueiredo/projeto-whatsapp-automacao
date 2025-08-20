# 🤖 Guia de Teste do Protótipo WhatsApp

## 📋 Visão Geral

Este guia explica como testar o protótipo de automação WhatsApp para transferências internacionais. O sistema está configurado para funcionar em modo de desenvolvimento com simulações.

## 🚀 Como Iniciar o Teste

### 1. Verificar se o Servidor está Rodando

```bash
cd backend
python manage.py runserver
```

O servidor deve estar acessível em: `http://127.0.0.1:8000`

### 2. Executar o Script de Teste

```bash
python test_whatsapp.py
```

## 🧪 Opções de Teste Disponíveis

### Opção 1: Teste do Fluxo Completo

Testa toda a jornada do usuário:
1. **Saudação inicial** - "Olá"
2. **Cadastro de CPF** - "12345678901"
3. **Valor da transferência** - "100" (USD)
4. **Nome do beneficiário** - "João Silva"
5. **CPF do beneficiário** - "12345678901"
6. **Confirmação** - "1"

### Opção 2: Teste de Mensagem Única

Permite testar mensagens específicas para verificar respostas individuais.

### Opção 3: Verificação do Status do Servidor

Confirma se o servidor Django está respondendo corretamente.

## 📱 Fluxo de Conversa Esperado

### 1. Início da Conversa
```
Usuário: Olá
Bot: Olá! 👋 Bem-vindo ao nosso serviço de transferências internacionais!
     Você já tem cadastro? Digite 1 para me cadastrar ou 2 para não agora.
```

### 2. Processo de Cadastro
```
Usuário: 1
Bot: Ótimo! Para começar, qual o seu nome completo?

Usuário: [Nome]
Bot: Prazer, [Nome]! Agora, por favor, crie um nome de usuário:

Usuário: [Username]
Bot: Perfeito! Agora preciso do seu CPF (apenas números):
```

### 3. Processo de Transferência
```
Bot: Quanto você gostaria de enviar? (valor em USD)

Usuário: 100
Bot: Você quer enviar $100.00 USD.
     Taxa atual: 1 USD = 5.20 BRL
     Valor em reais: R$ 520.00
     
     Qual o nome completo do beneficiário?

Usuário: João Silva
Bot: Qual o CPF do beneficiário? (apenas números)

Usuário: 12345678901
Bot: 📋 Resumo da Transferência:
     • Valor: $100.00 USD
     • Para: João Silva
     • CPF: 123.456.789-01
     • Você receberá: R$ 520.00
     
     Confirma? Digite 1 para SIM ou 2 para NÃO
```

### 4. Confirmação e Pagamento
```
Usuário: 1
Bot: ✅ Transferência confirmada!
     
     Para finalizar, clique no link abaixo para efetuar o pagamento:
     [Link de Pagamento]
     
     ID da transferência: TXN_[ID]
```

## 🔧 Configurações de Teste

### Arquivo .env
O sistema usa as seguintes configurações para teste:

```env
# WhatsApp Cloud API (Modo Teste)
WHATSAPP_ACCESS_TOKEN=test_token
WHATSAPP_PHONE_NUMBER_ID=123456789
WHATSAPP_VERIFY_TOKEN=test_verify_token

# Pagamentos (Modo Teste)
PAYMENT_PROVIDER=stripe
PAYMENT_API_KEY=sk_test_example
```

### Número de Teste
O script usa o número `+5511999999999` para simular conversas.

## 📊 Monitoramento dos Testes

### Logs do Servidor
Durante os testes, você pode acompanhar os logs no terminal onde o servidor está rodando:

```
INFO MOCK: Sending to 5511999999999: [Mensagem do Bot]
INFO WhatsApp response sent to 5511999999999: [Resposta da API]
INFO "POST /api/webhook/ HTTP/1.1" 200 20
```

### Painel Administrativo
Acesse `http://127.0.0.1:8000/admin/` para ver:
- **Usuários cadastrados**
- **Conversas ativas**
- **Transferências criadas**
- **Logs de webhook**

**Credenciais do Admin:**
- Usuário: `admin`
- Senha: `admin123`

## 🐛 Solução de Problemas

### Erro de Conexão
```
❌ Erro de conexão: [erro]
```
**Solução:** Verifique se o servidor Django está rodando.

### Status 500
```
📊 Status: 500
❌ Erro: Internal Server Error
```
**Solução:** Verifique os logs do servidor para detalhes do erro.

### Webhook não Responde
```
📊 Status: 404
❌ Erro: Not Found
```
**Solução:** Verifique se a URL do webhook está correta: `/api/webhook/`

## 🔄 Testando com WhatsApp Real

Para testar com WhatsApp real, você precisará:

1. **Configurar WhatsApp Cloud API:**
   - Criar uma conta no Meta for Developers
   - Configurar um app WhatsApp Business
   - Obter tokens de acesso reais

2. **Configurar Webhook Público:**
   - Usar ngrok ou similar para expor o servidor local
   - Configurar a URL do webhook no Meta

3. **Atualizar .env:**
   ```env
   WHATSAPP_ACCESS_TOKEN=[seu_token_real]
   WHATSAPP_PHONE_NUMBER_ID=[seu_phone_id]
   WHATSAPP_WEBHOOK_URL=[sua_url_publica]/api/webhook/
   ```

## 📈 Próximos Passos

Após os testes locais, você pode:

1. **Integrar pagamentos reais** (Stripe/MercadoPago)
2. **Configurar APIs de cotação reais**
3. **Implementar notificações por email**
4. **Adicionar mais validações de segurança**
5. **Deploy em produção**

## 📞 Suporte

Se encontrar problemas durante os testes:

1. Verifique os logs do servidor
2. Confirme as configurações do .env
3. Teste cada componente individualmente
4. Consulte a documentação da API do WhatsApp

---

**✅ Status do Teste:** O protótipo está funcionando corretamente em modo de desenvolvimento!