#!/usr/bin/env python
"""
Script para testar o protótipo WhatsApp localmente
Simula mensagens enviadas pelo WhatsApp Cloud API
"""

import requests
import json
import time

# Configurações
BASE_URL = "http://127.0.0.1:8000"
WEBHOOK_URL = f"{BASE_URL}/api/webhook/"
TEST_PHONE = "+5511999999999"  # Número de teste

def simulate_whatsapp_message(phone, message):
    """
    Simula uma mensagem recebida do WhatsApp Cloud API
    """
    # Estrutura de dados similar ao WhatsApp Cloud API
    webhook_data = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "123456789",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "15550123456",
                        "phone_number_id": "123456789"
                    },
                    "contacts": [{
                        "profile": {
                            "name": "Usuário Teste"
                        },
                        "wa_id": phone.replace("+", "")
                    }],
                    "messages": [{
                        "from": phone.replace("+", ""),
                        "id": f"msg_{int(time.time())}",
                        "timestamp": str(int(time.time())),
                        "text": {
                            "body": message
                        },
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=webhook_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📱 Mensagem enviada: '{message}'")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Resposta: {response.json()}")
        else:
            print(f"❌ Erro: {response.text}")
            
        return response
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return None

def test_conversation_flow():
    """
    Testa o fluxo completo de conversa
    """
    print("🚀 Iniciando teste do protótipo WhatsApp...\n")
    
    # Sequência de mensagens para testar o fluxo
    test_messages = [
        "Olá",
        "12345678901",  # CPF de teste
        "100",          # Valor em USD
        "João Silva",   # Nome do beneficiário
        "12345678901",  # CPF do beneficiário
        "1",            # Confirmação
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Passo {i} ---")
        response = simulate_whatsapp_message(TEST_PHONE, message)
        
        if response:
            print("⏳ Aguardando 2 segundos...")
            time.sleep(2)
        else:
            print("❌ Falha na comunicação. Interrompendo teste.")
            break
    
    print("\n🏁 Teste concluído!")

def test_single_message(message):
    """
    Testa uma única mensagem
    """
    print(f"🧪 Testando mensagem única: '{message}'\n")
    simulate_whatsapp_message(TEST_PHONE, message)

def check_server_status():
    """
    Verifica se o servidor está rodando
    """
    try:
        response = requests.get(f"{BASE_URL}/admin/", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor Django está rodando")
            return True
        else:
            print(f"⚠️  Servidor respondeu com status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ Servidor Django não está acessível")
        return False

def main():
    """
    Menu principal
    """
    print("=" * 50)
    print("🤖 TESTE DO PROTÓTIPO WHATSAPP")
    print("=" * 50)
    
    # Verificar se o servidor está rodando
    if not check_server_status():
        print("\n❌ Certifique-se de que o servidor Django está rodando:")
        print("   cd backend && python manage.py runserver")
        return
    
    while True:
        print("\n📋 Opções de teste:")
        print("1 - Testar fluxo completo de conversa")
        print("2 - Enviar mensagem única")
        print("3 - Verificar status do servidor")
        print("0 - Sair")
        
        choice = input("\n👉 Escolha uma opção: ").strip()
        
        if choice == "1":
            test_conversation_flow()
        elif choice == "2":
            message = input("Digite a mensagem: ").strip()
            if message:
                test_single_message(message)
        elif choice == "3":
            check_server_status()
        elif choice == "0":
            print("👋 Até logo!")
            break
        else:
            print("❌ Opção inválida")

if __name__ == "__main__":
    main()