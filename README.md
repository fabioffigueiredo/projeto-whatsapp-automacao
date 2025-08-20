# WhatsApp Automation - Sistema de Transferências Internacionais

🚀 Sistema automatizado para transferências internacionais via WhatsApp Cloud API, integrado com APIs de câmbio e pagamento.

## 📋 Funcionalidades

- ✅ **Integração WhatsApp Cloud API** - Comunicação automatizada via WhatsApp
- ✅ **Cotação de Câmbio** - Consulta de taxas em tempo real (Fixer.io)
- ✅ **Processamento de Pagamentos** - Links de pagamento seguros
- ✅ **Validação de CPF** - Verificação de documentos via XPS247
- ✅ **Webhook de Pagamentos** - Notificações automáticas
- ✅ **Sistema de Logs** - Rastreamento completo de operações
- ✅ **API REST** - Endpoints para integração
- ✅ **Containerização** - Docker + Docker Compose

## 🛠️ Tecnologias

- **Backend**: Django 5.1 + Django REST Framework
- **Banco de Dados**: PostgreSQL / SQLite
- **Cache**: Redis
- **Containerização**: Docker + Docker Compose
- **APIs Externas**: WhatsApp Cloud API, Fixer.io, XPS247
- **Automação**: n8n (opcional)

## 🚀 Instalação Rápida

### Opção 1: Setup Automático

```bash
# Clone o repositório
git clone <repository-url>
cd projeto-whatsapp-automacao

# Execute o setup automático
python setup.py
```

### Opção 2: Docker (Recomendado)

```bash
# Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações

# Inicie os serviços
docker-compose up -d

# Acesse a aplicação
# Backend: http://localhost:8000
# Admin: http://localhost:8000/admin
# n8n: http://localhost:5678
```

## ⚙️ Configuração

### Variáveis de Ambiente

Configure as seguintes variáveis no arquivo `.env`:

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True

# WhatsApp Cloud API
WHATSAPP_ACCESS_TOKEN=your-whatsapp-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_VERIFY_TOKEN=your-verify-token

# APIs Externas
FIXER_API_KEY=your-fixer-api-key
XPS247_API_KEY=your-xps247-api-key

# Pagamentos
PAYMENT_WEBHOOK_SECRET=your-webhook-secret
```

## 📱 Fluxo de Uso

1. **Cliente inicia conversa** - Envia mensagem para o WhatsApp Business
2. **Validação de CPF** - Sistema solicita e valida CPF
3. **Cotação** - Consulta taxa de câmbio atual
4. **Confirmação** - Cliente confirma valores e dados
5. **Pagamento** - Sistema gera link de pagamento
6. **Processamento** - Webhook confirma pagamento
7. **Notificação** - Cliente recebe confirmação

## 🔧 Estratégia de Desenvolvimento

### Sprint 1 - Protótipo Básico ✅
- ✅ Backend Django com estrutura completa
- ✅ Modelos para conversas, operações e clientes
- ✅ API REST para webhooks
- ✅ Integração com WhatsApp Cloud API
- ✅ Serviços para APIs externas
- ✅ Sistema de logs
- ✅ Containerização Docker

### Sprint 2 - Protótipo Funcional
- Gateway de pagamento real (MercadoPago/Stripe)
- Dashboard administrativo
- Testes automatizados

### Sprint 3 - Produção Inicial
- Deploy em cloud (Render/Railway)
- Monitoramento e alertas
- Backup automatizado

### Sprint 4 - Escalabilidade
- Load balancing
- Cache distribuído
- Métricas avançadas

## Estrutura do Projeto
```
whatsapp-automation/
├── backend/
│   ├── config/         # Configurações Django
│   ├── core/           # App principal
│   │   ├── models.py   # Modelos de dados
│   │   ├── views.py    # APIs e webhooks
│   │   └── services/   # Integrações externas
│   └── manage.py
├── n8n/
│   └── workflow.json   # Fluxo de automação
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Rodando com Docker
```bash
cp .env.example .env
docker-compose up -d --build
```

## Endpoints Principais
- `http://localhost:8000/api/conversations/` → Gerenciar conversas
- `http://localhost:8000/api/rates/` → Consultar câmbio atual

## Workflow n8n
Importar o arquivo `n8n/workflow.json` no painel do n8n.

## Autenticação
A API usa autenticação JWT (JSON Web Token).
