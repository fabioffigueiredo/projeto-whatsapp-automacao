# Manual Completo - Admin Bot (Passo a Passo)

Este manual foi feito para iniciantes, cobrindo do zero até rodar o sistema.

---

## 1. Clonar o Repositório
```bash
git clone https://github.com/seuusuario/admin-bot.git
cd admin-bot
```

## 2. Preparar Ambiente Virtual (sem Docker)
```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

## 3. Configurar Variáveis de Ambiente
Copie o arquivo de exemplo:
```bash
cp .env.example .env
```
Edite `.env` e configure seu banco de dados e chave secreta.

## 4. Migrar Banco de Dados
```bash
python manage.py migrate
python manage.py createsuperuser
```

## 5. Rodar o Servidor Django
```bash
python manage.py runserver
```

Acesse: [http://localhost:8000/admin](http://localhost:8000/admin)

---

## 6. Rodando com Docker (Recomendado)
```bash
docker-compose up -d --build
```

- Django → `http://localhost:8000`
- n8n → `http://localhost:5678`

---

## 7. Importar Workflow n8n
- Acesse `http://localhost:5678`
- Login → Import → `n8n/workflow.json`
- Publique

---

## 8. Testar
- Inicie uma conversa no WhatsApp configurado no n8n
- Veja a resposta automática com o valor do câmbio
- Teste CRUD no Django Admin

---

## 9. Boas Práticas
- Versione seu código com `git`
- Use `.env` para segredos (nunca comite senhas)
- Crie testes unitários com `pytest`
- Use Docker em produção
- Aplique técnicas de **UX/UI** (simplicidade, clareza, feedback rápido)
