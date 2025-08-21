#!/usr/bin/env python3
"""
Script de teste para integração n8n com Django
Testa todos os endpoints de integração do n8n
"""

import os
import sys
import django
import requests
import json
from datetime import datetime
import time

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

# URLs base
DJANGO_BASE_URL = "http://localhost:8000/api"
N8N_BASE_URL = "http://localhost:5678"

def test_django_endpoints():
    """Testa endpoints Django para integração n8n"""
    print("🧪 Testando endpoints Django para n8n...")
    
    # Teste 1: Analytics
    print("\n📊 Testando endpoint de analytics...")
    analytics_data = {
        "phone": "5511999999999",
        "message": "Teste de analytics",
        "conversationState": "NODE_1_GREETING",
        "responseTime": 150,
        "success": True,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{DJANGO_BASE_URL}/n8n/analytics/",
            json=analytics_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Analytics: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Analytics: Erro - {str(e)}")
    
    # Teste 2: Notificações
    print("\n📱 Testando endpoint de notificações...")
    notification_data = {
        "phone": "5511999999999",
        "type": "payment_initiated",
        "data": {
            "amount": 100.00,
            "payment_id": "pay_test_123"
        }
    }
    
    try:
        response = requests.post(
            f"{DJANGO_BASE_URL}/n8n/notifications/",
            json=notification_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Notificações: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Notificações: Erro - {str(e)}")
    
    # Teste 3: Pagamentos
    print("\n💳 Testando endpoint de pagamentos...")
    payment_data = {
        "phone": "5511999999999",
        "amount": 100.00
    }
    
    try:
        response = requests.post(
            f"{DJANGO_BASE_URL}/n8n/payments/",
            json=payment_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Pagamentos: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Pagamentos: Erro - {str(e)}")
    
    # Teste 4: Webhook genérico
    print("\n🔗 Testando webhook genérico...")
    webhook_data = {
        "type": "payment_status",
        "payment_id": "pay_test_123",
        "status": "completed",
        "phone": "5511999999999"
    }
    
    try:
        response = requests.post(
            f"{DJANGO_BASE_URL}/n8n/webhook/",
            json=webhook_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Webhook: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Webhook: Erro - {str(e)}")

def test_n8n_connectivity():
    """Testa conectividade com n8n"""
    print("\n🔌 Testando conectividade com n8n...")
    
    try:
        response = requests.get(f"{N8N_BASE_URL}/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ n8n está rodando e acessível")
            return True
        else:
            print(f"⚠️ n8n respondeu com status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ n8n não está acessível. Verifique se está rodando.")
        return False
    except Exception as e:
        print(f"❌ Erro ao conectar com n8n: {str(e)}")
        return False

def test_n8n_webhook():
    """Testa webhook do n8n (se estiver configurado)"""
    print("\n📡 Testando webhook do n8n...")
    
    # Simula dados do WhatsApp
    whatsapp_data = {
        "phone": "5511999999999",
        "message": "Teste de integração n8n",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Tenta enviar para o webhook do n8n
        response = requests.post(
            f"{N8N_BASE_URL}/webhook/whatsapp-webhook",
            json=whatsapp_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"✅ Webhook n8n: {response.status_code} - {response.text[:100]}...")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Webhook n8n não está configurado ou acessível")
        return False
    except Exception as e:
        print(f"❌ Erro no webhook n8n: {str(e)}")
        return False

def test_full_integration():
    """Testa integração completa n8n -> Django"""
    print("\n🔄 Testando integração completa...")
    
    # Simula fluxo completo:
    # 1. Webhook recebe mensagem
    # 2. n8n processa
    # 3. Django responde
    # 4. Analytics são coletados
    
    test_data = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "5511999999999",
                        "text": {"body": "Olá, quero fazer uma transferência"},
                        "type": "text"
                    }]
                }
            }]
        }]
    }
    
    try:
        # Simula webhook do WhatsApp para n8n
        response = requests.post(
            f"{N8N_BASE_URL}/webhook/whatsapp-webhook",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            print("✅ Integração completa funcionando")
            print(f"📄 Resposta: {response.json()}")
            return True
        else:
            print(f"⚠️ Integração com problemas: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na integração completa: {str(e)}")
        return False

def check_docker_services():
    """Verifica se os serviços Docker estão rodando"""
    print("🐳 Verificando serviços Docker...")
    
    services = {
        "Django": "http://localhost:8000/admin/",
        "n8n": "http://localhost:5678",
        "PostgreSQL": "localhost:5432",
        "Redis": "localhost:6379"
    }
    
    for service, url in services.items():
        try:
            if service in ["PostgreSQL", "Redis"]:
                # Para estes, apenas verificamos se a porta está aberta
                import socket
                host, port = url.split(":")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((host, int(port)))
                sock.close()
                if result == 0:
                    print(f"✅ {service} está rodando")
                else:
                    print(f"❌ {service} não está acessível")
            else:
                response = requests.get(url, timeout=5)
                if response.status_code in [200, 401, 403]:  # 401/403 são OK (auth required)
                    print(f"✅ {service} está rodando")
                else:
                    print(f"⚠️ {service} respondeu com status: {response.status_code}")
        except Exception as e:
            print(f"❌ {service} não está acessível: {str(e)}")

def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes de integração n8n...\n")
    
    # Verificar serviços Docker
    check_docker_services()
    
    # Testar conectividade n8n
    n8n_ok = test_n8n_connectivity()
    
    # Testar endpoints Django
    test_django_endpoints()
    
    # Testar webhook n8n (se disponível)
    if n8n_ok:
        test_n8n_webhook()
        
        # Aguardar um pouco e testar integração completa
        print("\n⏳ Aguardando 3 segundos...")
        time.sleep(3)
        test_full_integration()
    
    print("\n🏁 Testes concluídos!")
    print("\n📋 Próximos passos:")
    print("1. Verifique se todos os serviços estão rodando")
    print("2. Configure workflows no n8n (http://localhost:5678)")
    print("3. Importe os workflows da pasta n8n/")
    print("4. Configure webhooks do WhatsApp para apontar para n8n")
    print("5. Teste com mensagens reais do WhatsApp")

if __name__ == "__main__":
    main()