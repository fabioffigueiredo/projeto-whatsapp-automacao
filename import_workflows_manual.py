#!/usr/bin/env python3
"""
Script para importar workflows do N8N manualmente
"""

import requests
import json
import os
from pathlib import Path

def import_workflow_via_web():
    """Importa workflows através da interface web do N8N"""
    
    print("🚀 Importação manual de workflows do N8N")
    print("="*50)
    
    # URLs do N8N
    base_url = "http://localhost:5678"
    
    # Verificar se N8N está rodando
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ N8N está rodando")
        else:
            print(f"❌ N8N retornou status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao conectar com N8N: {e}")
        return False
    
    # Carregar workflows
    workflow_files = [
        "n8n/workflow.json",
        "n8n/advanced-workflow.json"
    ]
    
    for workflow_file in workflow_files:
        if os.path.exists(workflow_file):
            print(f"📁 Encontrado: {workflow_file}")
            
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                
                print(f"📋 Workflow: {workflow_data.get('name', 'Sem nome')}")
                print(f"📝 Descrição: {workflow_data.get('meta', {}).get('description', 'Sem descrição')}")
                print(f"🔗 Nodes: {len(workflow_data.get('nodes', []))}")
                
                # Instruções para importação manual
                print(f"\n📌 Para importar {workflow_file}:")
                print(f"   1. Acesse: {base_url}")
                print(f"   2. Faça login com: admin / admin")
                print(f"   3. Clique em 'Import from file'")
                print(f"   4. Selecione o arquivo: {os.path.abspath(workflow_file)}")
                print(f"   5. Ative o workflow após importar")
                print()
                
            except json.JSONDecodeError as e:
                print(f"❌ Erro ao ler {workflow_file}: {e}")
            except Exception as e:
                print(f"❌ Erro inesperado com {workflow_file}: {e}")
        else:
            print(f"❌ Arquivo não encontrado: {workflow_file}")
    
    # Verificar webhooks após importação
    print("\n🔍 Após importar, teste os webhooks:")
    print(f"   • Webhook básico: {base_url}/webhook/whatsapp-hook")
    print(f"   • Webhook teste: {base_url}/webhook/whatsapp-test")
    
    return True

def check_webhooks():
    """Verifica se os webhooks estão funcionando"""
    
    print("\n🔍 Verificando webhooks do N8N...")
    
    webhooks = [
        "http://localhost:5678/webhook/whatsapp-hook",
        "http://localhost:5678/webhook/whatsapp-test"
    ]
    
    for webhook_url in webhooks:
        try:
            response = requests.post(
                webhook_url,
                json={"test": "message", "from": "test"},
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"✅ Webhook funcionando: {webhook_url}")
            else:
                print(f"⚠️ Webhook retornou {response.status_code}: {webhook_url}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro no webhook {webhook_url}: {e}")

if __name__ == "__main__":
    import_workflow_via_web()
    check_webhooks()
    
    print("\n✨ Importação manual concluída!")
    print("\n📋 Próximos passos:")
    print("   1. Acesse http://localhost:5678")
    print("   2. Faça login com admin/admin")
    print("   3. Importe os workflows manualmente")
    print("   4. Ative os workflows")
    print("   5. Teste os webhooks")