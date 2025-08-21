#!/usr/bin/env python3
"""
Script de configuração automática do n8n
Configura workflows e integrações necessárias
"""

import os
import json
import requests
import time
import subprocess
from pathlib import Path

# Configurações
N8N_URL = "http://localhost:5678"
N8N_USER = os.getenv("N8N_USER", "admin")
N8N_PASSWORD = os.getenv("N8N_PASSWORD", "admin123")
PROJECT_ROOT = Path(__file__).parent

def check_docker_compose():
    """Verifica se o docker-compose está rodando"""
    print("🐳 Verificando Docker Compose...")
    
    try:
        result = subprocess.run(
            ["docker-compose", "ps"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        if "n8n" in result.stdout:
            print("✅ n8n container está rodando")
            return True
        else:
            print("❌ n8n container não está rodando")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar Docker: {str(e)}")
        return False

def start_services():
    """Inicia os serviços necessários"""
    print("🚀 Iniciando serviços...")
    
    try:
        # Iniciar apenas os serviços necessários
        subprocess.run(
            ["docker-compose", "up", "-d", "db", "redis", "n8n"],
            cwd=PROJECT_ROOT,
            check=True
        )
        
        print("✅ Serviços iniciados")
        print("⏳ Aguardando n8n inicializar...")
        
        # Aguardar n8n estar pronto
        for i in range(30):  # 30 tentativas = 1 minuto
            try:
                response = requests.get(f"{N8N_URL}/healthz", timeout=3)
                if response.status_code == 200:
                    print("✅ n8n está pronto!")
                    return True
            except:
                pass
            
            time.sleep(2)
            print(f"⏳ Tentativa {i+1}/30...")
        
        print("❌ n8n não ficou pronto a tempo")
        return False
        
    except Exception as e:
        print(f"❌ Erro ao iniciar serviços: {str(e)}")
        return False

def wait_for_n8n():
    """Aguarda n8n estar disponível"""
    print("⏳ Aguardando n8n estar disponível...")
    
    for i in range(30):
        try:
            response = requests.get(f"{N8N_URL}/healthz", timeout=3)
            if response.status_code == 200:
                print("✅ n8n está disponível!")
                return True
        except:
            pass
        
        time.sleep(2)
        if i % 5 == 0:
            print(f"⏳ Ainda aguardando... ({i+1}/30)")
    
    print("❌ n8n não ficou disponível")
    return False

def get_auth_token():
    """Obtém token de autenticação do n8n"""
    print("🔐 Obtendo token de autenticação...")
    
    try:
        # Primeiro, tentar login
        login_data = {
            "email": N8N_USER,
            "password": N8N_PASSWORD
        }
        
        response = requests.post(
            f"{N8N_URL}/rest/login",
            json=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            # Extrair token dos cookies ou headers
            cookies = response.cookies
            print("✅ Autenticação realizada")
            return cookies
        else:
            print(f"❌ Falha na autenticação: {response.status_code}")
            print(f"Resposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro na autenticação: {str(e)}")
        return None

def import_workflow(workflow_file, cookies=None):
    """Importa um workflow para o n8n"""
    workflow_path = PROJECT_ROOT / "n8n" / workflow_file
    
    if not workflow_path.exists():
        print(f"❌ Arquivo de workflow não encontrado: {workflow_path}")
        return False
    
    print(f"📥 Importando workflow: {workflow_file}")
    
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
        
        # Preparar dados para importação
        import_data = {
            "workflow": workflow_data
        }
        
        response = requests.post(
            f"{N8N_URL}/rest/workflows",
            json=import_data,
            cookies=cookies,
            timeout=15
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ Workflow {workflow_file} importado com sucesso")
            return True
        else:
            print(f"❌ Falha ao importar {workflow_file}: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao importar {workflow_file}: {str(e)}")
        return False

def activate_workflow(workflow_name, cookies=None):
    """Ativa um workflow no n8n"""
    print(f"🔄 Ativando workflow: {workflow_name}")
    
    try:
        # Primeiro, listar workflows para encontrar o ID
        response = requests.get(
            f"{N8N_URL}/rest/workflows",
            cookies=cookies,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Erro ao listar workflows: {response.status_code}")
            return False
        
        workflows = response.json()
        workflow_id = None
        
        for workflow in workflows:
            if workflow.get('name') == workflow_name:
                workflow_id = workflow.get('id')
                break
        
        if not workflow_id:
            print(f"❌ Workflow '{workflow_name}' não encontrado")
            return False
        
        # Ativar o workflow
        response = requests.patch(
            f"{N8N_URL}/rest/workflows/{workflow_id}/activate",
            cookies=cookies,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Workflow '{workflow_name}' ativado")
            return True
        else:
            print(f"❌ Erro ao ativar workflow: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao ativar workflow: {str(e)}")
        return False

def setup_environment():
    """Configura variáveis de ambiente"""
    print("🔧 Configurando ambiente...")
    
    env_file = PROJECT_ROOT / ".env"
    
    # Verificar se .env existe
    if not env_file.exists():
        print("📝 Criando arquivo .env...")
        
        env_content = f"""# Configurações n8n
N8N_USER={N8N_USER}
N8N_PASSWORD={N8N_PASSWORD}
N8N_WEBHOOK_URL=http://localhost:5678/webhook

# Configurações Django
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/whatsapp_db
REDIS_URL=redis://localhost:6379/0

# WhatsApp
WHATSAPP_TOKEN=your-whatsapp-token
WHATSAPP_VERIFY_TOKEN=your-verify-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
"""
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ Arquivo .env criado")
    else:
        print("✅ Arquivo .env já existe")

def create_test_webhook():
    """Cria webhook de teste"""
    print("🔗 Configurando webhook de teste...")
    
    webhook_url = f"{N8N_URL}/webhook/whatsapp-test"
    
    test_data = {
        "phone": "5511999999999",
        "message": "Teste de configuração",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=test_data,
            timeout=10
        )
        
        print(f"📡 Teste de webhook: {response.status_code}")
        if response.status_code == 200:
            print("✅ Webhook funcionando")
        else:
            print("⚠️ Webhook pode precisar de configuração")
            
    except Exception as e:
        print(f"⚠️ Webhook ainda não configurado: {str(e)}")

def main():
    """Função principal de configuração"""
    print("🎯 Configuração automática do n8n\n")
    
    # 1. Configurar ambiente
    setup_environment()
    
    # 2. Verificar se Docker está rodando
    if not check_docker_compose():
        print("\n🚀 Iniciando serviços Docker...")
        if not start_services():
            print("❌ Falha ao iniciar serviços")
            return
    
    # 3. Aguardar n8n
    if not wait_for_n8n():
        print("❌ n8n não está disponível")
        return
    
    # 4. Autenticar
    cookies = get_auth_token()
    
    # 5. Importar workflows
    workflows = ["workflow.json", "advanced-workflow.json"]
    
    for workflow in workflows:
        import_workflow(workflow, cookies)
    
    # 6. Ativar workflows
    workflow_names = [
        "WhatsApp Orchestrator (Django API)",
        "WhatsApp Advanced Integration"
    ]
    
    for name in workflow_names:
        activate_workflow(name, cookies)
    
    # 7. Teste básico
    create_test_webhook()
    
    print("\n🎉 Configuração concluída!")
    print("\n📋 Próximos passos:")
    print(f"1. Acesse n8n: {N8N_URL}")
    print(f"2. Login: {N8N_USER} / {N8N_PASSWORD}")
    print("3. Verifique se os workflows estão ativos")
    print("4. Configure webhooks do WhatsApp")
    print("5. Execute: python test_n8n_integration.py")
    
    print("\n🔗 URLs importantes:")
    print(f"- n8n Interface: {N8N_URL}")
    print(f"- Django Admin: http://localhost:8000/admin/")
    print(f"- API Docs: http://localhost:8000/api/")
    print(f"- Webhook Test: {N8N_URL}/webhook/whatsapp-test")

if __name__ == "__main__":
    main()