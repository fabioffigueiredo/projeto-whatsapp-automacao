# Política de Segurança

## Versões Suportadas

Atualmente, apenas a versão mais recente do branch `main` recebe atualizações de segurança.

| Versão | Suportada |
|--------|----------|
| main   | Sim |

## Reportando Vulnerabilidades

Se você descobriu uma vulnerabilidade de segurança neste repositório, **não abra uma issue pública**.

Por favor, reporte de forma privada utilizando um dos canais abaixo:

- **GitHub Private Vulnerability Reporting**: Use a aba [Security > Report a vulnerability](../../security/advisories/new)
- **Email**: Entre em contato diretamente com o mantenedor do repositório

### O que incluir no relato

1. Descrição detalhada da vulnerabilidade
2. Passos para reproduzir o problema
3. Impacto potencial (confidencialidade, integridade, disponibilidade)
4. Versão/commit afetado
5. Sugestão de correção (opcional)

## Tempo de Resposta

- **Confirmação de recebimento**: Até 48 horas
- **Avaliação inicial**: Até 7 dias
- **Correção e divulgação**: Até 30 dias (dependendo da complexidade)

## Boas Práticas de Segurança deste Projeto

- Nunca commite arquivos `.env` com credenciais reais
- Use sempre o arquivo `.env.example` como template
- Todas as chaves de API e tokens devem ser rotacionados após exposição
- O banco de dados SQLite (`db.sqlite3`) nunca deve ser versionado
- Credenciais do WhatsApp Cloud API devem ser protegidas como segredos de produção

## Histórico de Segurança

| Data | Descrição | Status |
|------|-----------|--------|
| 2026-05-12 | Remoção de credenciais reais expostas no `backend/.env` | Corrigido |
| 2026-05-12 | Remoção do banco de dados `db.sqlite3` do repositório público | Corrigido |
| 2026-05-12 | Habilitação de Secret Scanning e Dependabot | Implementado |
