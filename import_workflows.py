#!/usr/bin/env python3
"""
Script para importar workflows do N8N manualmente
"""

import requests
import json
import time
from pathlib import Path

# Configurações
N8N_URL = "http://localhost:5678"
N8N_USER = "admin"
N8N_PASSWORD = "admin123"

def get_auth_token():
    """Obtém token de autenticação do N8N"""
    print("🔐 Obtendo token de autenticação...")
    
    # Primeiro, vamos tentar fazer login
    login_data = {
        "email": N8N_USER,
        "password": N8N_PASSWORD
    }
    
    try:
        response = requests.post(f"{N8N_URL}/rest/login", json=login_data)
        if response.status_code == 200:
            print("✅ Login realizado com sucesso")
            return response.cookies
        else:
            print(f"❌ Falha no login: {response.status_code}")
            print(f"Resposta: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erro no login: {e}")
        return None

def import_workflow(workflow_file, cookies):
    """Importa um workflow específico"""
    print(f"📥 Importando workflow: {workflow_file}")
    
    try:
        # Lê o arquivo do workflow
        with open(workflow_file, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
        
        # Importa o workflow
        response = requests.post(
            f"{N8N_URL}/rest/workflows/import",
            json=workflow_data,
            cookies=cookies
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ Workflow {workflow_file} importado com sucesso")
            return True
        else:
            print(f"❌ Falha ao importar {workflow_file}: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao importar {workflow_file}: {e}")
        return False

def activate_workflow(workflow_name, cookies):
    """Ativa um workflow específico"""
    print(f"🔄 Ativando workflow: {workflow_name}")
    
    try:
        # Lista todos os workflows para encontrar o ID
        response = requests.get(f"{N8N_URL}/rest/workflows", cookies=cookies)
        
        if response.status_code != 200:
            print(f"❌ Erro ao listar workflows: {response.status_code}")
            return False
        
        workflows = response.json()
        workflow_id = None
        
        # Procura o workflow pelo nome
        for workflow in workflows:
            if workflow.get('name') == workflow_name:
                workflow_id = workflow.get('id')
                break
        
        if not workflow_id:
            print(f"❌ Workflow '{workflow_name}' não encontrado")
            return False
        
        # Ativa o workflow
        response = requests.patch(
            f"{N8N_URL}/rest/workflows/{workflow_id}/activate",
            cookies=cookies
        )
        
        if response.status_code == 200:
            print(f"✅ Workflow '{workflow_name}' ativado com sucesso")
            return True
        else:
            print(f"❌ Falha ao ativar '{workflow_name}': {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao ativar workflow: {e}")
        return False

def list_workflows(cookies):
    """Lista todos os workflows"""
    print("📋 Listando workflows...")
    
    try:
        response = requests.get(f"{N8N_URL}/rest/workflows", cookies=cookies)
        
        if response.status_code == 200:
            workflows = response.json()
            print(f"\n📊 Total de workflows: {len(workflows)}")
            
            for workflow in workflows:
                name = workflow.get('name', 'Sem nome')
                active = workflow.get('active', False)
                workflow_id = workflow.get('id')
                status = "🟢 Ativo" if active else "🔴 Inativo"
                print(f"  - {name} (ID: {workflow_id}) - {status}")
            
            return workflows
        else:
            print(f"❌ Erro ao listar workflows: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Erro ao listar workflows: {e}")
        return []

def main():
    print("🚀 Importando workflows do N8N")
    print("=" * 50)
    
    # Obtém token de autenticação
    cookies = get_auth_token()
    if not cookies:
        print("❌ Não foi possível autenticar. Verifique as credenciais.")
        return
    
    # Lista workflows existentes
    existing_workflows = list_workflows(cookies)
    
    # Workflows para importar
    workflow_files = [
        'workflow.json',
        'advanced-workflow.json'
    ]
    
    # Importa cada workflow
    imported_count = 0
    for workflow_file in workflow_files:
        if Path(workflow_file).exists():
            if import_workflow(workflow_file, cookies):
                imported_count += 1
        else:
            print(f"⚠️ Arquivo {workflow_file} não encontrado")
    
    print(f"\n📊 Workflows importados: {imported_count}/{len(workflow_files)}")
    
    # Lista workflows após importação
    print("\n" + "=" * 50)
    updated_workflows = list_workflows(cookies)
    
    # Ativa workflows importantes
    workflows_to_activate = [
        "WhatsApp Orchestrator (Django API)",
        "WhatsApp Advanced Integration"
    ]
    
    print("\n" + "=" * 50)
    for workflow_name in workflows_to_activate:
        activate_workflow(workflow_name, cookies)
    
    print("\n🎉 Importação concluída!")
    print("\n📋 Próximos passos:")
    print("1. Acesse N8N: http://localhost:5678")
    print("2. Verifique se os workflows estão ativos")
    print("3. Teste os webhooks")
    print("4. Execute: python test_n8n_integration.py")

if __name__ == "__main__":
    main()