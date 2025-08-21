#!/usr/bin/env python3
"""
Script simples para configurar N8N e importar workflows
"""

import requests
import json
import time
from pathlib import Path

# Configurações
N8N_URL = "http://localhost:5678"

def check_n8n_status():
    """Verifica o status do N8N"""
    print("🔍 Verificando status do N8N...")
    
    try:
        # Tenta acessar a página principal
        response = requests.get(f"{N8N_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ N8N está rodando")
            return True
        else:
            print(f"❌ N8N retornou status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar com N8N: {e}")
        return False

def setup_n8n_owner():
    """Configura o owner inicial do N8N"""
    print("🔧 Configurando owner do N8N...")
    
    setup_data = {
        "email": "admin@example.com",
        "firstName": "Admin",
        "lastName": "User",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{N8N_URL}/rest/owner/setup", json=setup_data)
        if response.status_code in [200, 201]:
            print("✅ Owner configurado com sucesso")
            return True
        elif response.status_code == 400:
            print("ℹ️ Owner já foi configurado")
            return True
        else:
            print(f"❌ Falha na configuração: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro na configuração: {e}")
        return False

def login_n8n():
    """Faz login no N8N"""
    print("🔐 Fazendo login no N8N...")
    
    login_data = {
        "email": "admin@example.com",
        "password": "admin123"
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

def copy_workflows_to_n8n():
    """Copia workflows diretamente para o diretório do N8N"""
    print("📁 Copiando workflows para o N8N...")
    
    # Como estamos usando Docker, vamos tentar via API ou criar workflows básicos
    workflows = [
        {
            "name": "WhatsApp Webhook Basic",
            "nodes": [
                {
                    "id": "webhook",
                    "name": "Webhook",
                    "type": "n8n-nodes-base.webhook",
                    "position": [250, 300],
                    "parameters": {
                        "path": "whatsapp-hook",
                        "httpMethod": "POST"
                    }
                },
                {
                    "id": "respond",
                    "name": "Respond to Webhook",
                    "type": "n8n-nodes-base.respondToWebhook",
                    "position": [450, 300],
                    "parameters": {
                        "respondWith": "text",
                        "responseBody": "OK"
                    }
                }
            ],
            "connections": {
                "webhook": {
                    "main": [[{"node": "respond", "type": "main", "index": 0}]]
                }
            },
            "active": True
        }
    ]
    
    return workflows

def create_basic_workflow(cookies):
    """Cria um workflow básico via API"""
    print("🔨 Criando workflow básico...")
    
    workflow_data = {
        "name": "WhatsApp Basic Webhook",
        "nodes": [
            {
                "id": "webhook-node",
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "position": [250, 300],
                "parameters": {
                    "path": "whatsapp-hook",
                    "httpMethod": "POST",
                    "responseMode": "responseNode"
                }
            },
            {
                "id": "respond-node",
                "name": "Respond",
                "type": "n8n-nodes-base.respondToWebhook",
                "position": [450, 300],
                "parameters": {
                    "respondWith": "json",
                    "responseBody": '{"status": "received", "message": "WhatsApp webhook processed"}'
                }
            }
        ],
        "connections": {
            "webhook-node": {
                "main": [[{"node": "respond-node", "type": "main", "index": 0}]]
            }
        },
        "active": True
    }
    
    try:
        response = requests.post(
            f"{N8N_URL}/rest/workflows",
            json=workflow_data,
            cookies=cookies
        )
        
        if response.status_code in [200, 201]:
            print("✅ Workflow básico criado com sucesso")
            return True
        else:
            print(f"❌ Falha ao criar workflow: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao criar workflow: {e}")
        return False

def main():
    print("🚀 Configuração simples do N8N")
    print("=" * 40)
    
    # Verifica se N8N está rodando
    if not check_n8n_status():
        print("❌ N8N não está disponível")
        return
    
    # Configura owner (se necessário)
    setup_n8n_owner()
    
    # Faz login
    cookies = login_n8n()
    if not cookies:
        print("❌ Não foi possível fazer login")
        return
    
    # Cria workflow básico
    create_basic_workflow(cookies)
    
    print("\n🎉 Configuração concluída!")
    print("\n📋 Próximos passos:")
    print("1. Acesse N8N: http://localhost:5678")
    print("2. Login: admin@example.com / admin123")
    print("3. Verifique o workflow criado")
    print("4. Teste: python test_n8n_integration.py")

if __name__ == "__main__":
    main()