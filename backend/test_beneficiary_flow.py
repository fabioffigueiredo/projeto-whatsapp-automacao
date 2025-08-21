#!/usr/bin/env python
"""
Script para testar o fluxo completo de cadastro de beneficiário
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api"
PHONE_NUMBER = "5511999999999"

def send_webhook_message(phone_number, message_text, message_id=None):
    """Envia mensagem simulada do WhatsApp"""
    url = f"{BASE_URL}/webhook/"
    
    if message_id is None:
        message_id = f"wamid.test{int(time.time())}"
    
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
                                    "from": phone_number,
                                    "id": message_id,
                                    "timestamp": str(int(time.time())),
                                    "text": {
                                        "body": message_text
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
    
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=webhook_data, headers=headers)
    return response

def get_last_response(phone_number):
    """Obtém a última resposta do sistema para um número"""
    try:
        response = requests.get(f"{BASE_URL}/conversation/last-response/{phone_number}/")
        if response.status_code == 200:
            data = response.json()
            return data.get('message', 'N/A'), data.get('state', 'N/A')
        else:
            print(f"Erro na requisição: {response.status_code} - {response.text}")
            return 'N/A', 'N/A'
    except Exception as e:
        print(f"Erro ao obter última resposta: {e}")
        return 'N/A', 'N/A'

def test_beneficiary_registration_flow():
    """Testa o fluxo completo de cadastro de beneficiário"""
    print("=== TESTE DO FLUXO DE CADASTRO DE BENEFICIÁRIO ===")
    
    # 1. Testar com CPF válido
    print("1. Enviando CPF válido (12345678901)...")
    response = send_webhook_message(PHONE_NUMBER, "12345678901")
    print(f"Status: {response.status_code}")

    # Aguardar um pouco para o processamento
    time.sleep(1)

    # Verificar resposta do sistema
    message, state = get_last_response(PHONE_NUMBER)
    print(f"Resposta do sistema: {message}")
    print(f"Estado da conversa: {state}")

    # 2. Se o sistema solicitar confirmação, responder "1"
    if "Digite 1 para cadastrar" in message:
        print("\n2. Respondendo '1' para cadastrar novo beneficiário...")
        response = send_webhook_message(PHONE_NUMBER, "1")
        print(f"Status: {response.status_code}")
        
        # Aguardar processamento
        time.sleep(1)
        
        # Verificar nova resposta
        message, state = get_last_response(PHONE_NUMBER)
        print(f"Resposta do sistema: {message}")
        print(f"Estado da conversa: {state}")
    else:
        print("\n2. Sistema não solicitou cadastro - testando resposta '1'...")
        response = send_webhook_message(PHONE_NUMBER, "1")
        print(f"Status: {response.status_code}")
        
        # Aguardar processamento
        time.sleep(1)
        
        # Verificar nova resposta
        message, state = get_last_response(PHONE_NUMBER)
        print(f"Resposta do sistema: {message}")
        print(f"Estado da conversa: {state}")

    # 3. Testar com CPF formatado
    print("\n3. Testando com CPF formatado (123.456.789-01)...")
    response = send_webhook_message(PHONE_NUMBER, "123.456.789-01")
    print(f"Status: {response.status_code}")

    # Aguardar processamento
    time.sleep(1)

    # Verificar resposta do sistema
    message, state = get_last_response(PHONE_NUMBER)
    print(f"Resposta do sistema: {message}")
    print(f"Estado da conversa: {state}")
    
    print("\n=== TESTE CONCLUÍDO ===")

if __name__ == "__main__":
    test_beneficiary_registration_flow()