#!/usr/bin/env python
"""
Script para testar o webhook do WhatsApp com dados simulados
"""

import requests
import json

def test_whatsapp_webhook():
    """Testa o webhook com dados simulados do WhatsApp"""
    
    # URL do webhook
    url = "http://localhost:8000/api/webhook/"
    
    # Dados simulados no formato do WhatsApp Cloud API
    webhook_data = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550123456",
                                "phone_number_id": "123456789"
                            },
                            "messages": [
                                {
                                    "from": "5511999999999",
                                    "id": "wamid.test123",
                                    "timestamp": "1692901234",
                                    "text": {
                                        "body": "oi"
                                    },
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("Enviando mensagem 'oi' para iniciar conversa...")
        response = requests.post(url, json=webhook_data, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.text}")
        
        # Verifica última resposta
        last_response_url = "http://localhost:8000/api/conversation/last-response/5511999999999/"
        response = requests.get(last_response_url)
        if response.status_code == 200:
            data = response.json()
            print(f"\nÚltima resposta do sistema: {data.get('last_message', 'N/A')}")
            print(f"Estado da conversa: {data.get('conversation_state', 'N/A')}")
        
        # Agora testa com CPF
        print("\n" + "="*50)
        print("Enviando CPF para testar busca de beneficiário...")
        
        webhook_data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"] = "123.456.789-01"
        webhook_data["entry"][0]["changes"][0]["value"]["messages"][0]["id"] = "wamid.test124"
        
        response = requests.post(url, json=webhook_data, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.text}")
        
        # Verifica última resposta novamente
        response = requests.get(last_response_url)
        if response.status_code == 200:
            data = response.json()
            print(f"\nÚltima resposta do sistema: {data.get('last_message', 'N/A')}")
            print(f"Estado da conversa: {data.get('conversation_state', 'N/A')}")
            
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    test_whatsapp_webhook()