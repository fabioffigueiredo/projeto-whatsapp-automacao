# Admin Bot - Sistema de Atendimento e Transferências

## Visão Geral
Este projeto integra **Django + DRF** com **n8n** para automatizar atendimentos via WhatsApp, incluindo consultas de câmbio e transferências.

## Tecnologias
- Python 3.11
- Django 5 + Django REST Framework
- PostgreSQL
- n8n (orquestração e automação)
- Docker + Docker Compose

## Estrutura
```
admin-bot-full/
├── backend/        # Código Django
├── n8n/            # Workflow exportado
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── README.md
└── README-BEGINNER.md
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
