#!/usr/bin/env python
"""
Teste completo do fluxo de cadastro de beneficiário
Simula todo o processo desde o CPF até a confirmação final
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
    
    payload = {
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
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, json=payload, headers=headers)
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

def wait_and_check_response(phone_number, step_name):
    """Aguarda e verifica a resposta do sistema"""
    time.sleep(1)
    message, state = get_last_response(phone_number)
    print(f"  Resposta: {message}")
    print(f"  Estado: {state}")
    return message, state

def test_complete_beneficiary_flow():
    """Testa o fluxo completo de cadastro de beneficiário"""
    print("=== TESTE COMPLETO DO FLUXO DE CADASTRO DE BENEFICIÁRIO ===")
    
    # 1. Enviar CPF que não existe
    print("\n1. Enviando CPF não cadastrado (11122233344)...")
    response = send_webhook_message(PHONE_NUMBER, "11122233344")
    print(f"Status: {response.status_code}")
    message, state = wait_and_check_response(PHONE_NUMBER, "CPF")
    
    # 2. Confirmar cadastro de novo beneficiário
    if "Digite 1 para cadastrar" in message:
        print("\n2. Confirmando cadastro de novo beneficiário (1)...")
        response = send_webhook_message(PHONE_NUMBER, "1")
        print(f"Status: {response.status_code}")
        message, state = wait_and_check_response(PHONE_NUMBER, "Confirmação")
    
    # 3. Inserir chave PIX
    if "chave PIX" in message:
        print("\n3. Inserindo chave PIX (joao@email.com)...")
        response = send_webhook_message(PHONE_NUMBER, "joao@email.com")
        print(f"Status: {response.status_code}")
        message, state = wait_and_check_response(PHONE_NUMBER, "PIX")
    
    # 4. Inserir endereço
    if "endereço" in message:
        print("\n4. Inserindo endereço (Rua das Flores, 123, São Paulo, SP)...")
        response = send_webhook_message(PHONE_NUMBER, "Rua das Flores, 123, São Paulo, SP")
        print(f"Status: {response.status_code}")
        message, state = wait_and_check_response(PHONE_NUMBER, "Endereço")
    
    # 5. Inserir valor
    if "valor" in message:
        print("\n5. Inserindo valor (100)...")
        response = send_webhook_message(PHONE_NUMBER, "100")
        print(f"Status: {response.status_code}")
        message, state = wait_and_check_response(PHONE_NUMBER, "Valor")
    
    # 6. Confirmar dados
    if "Confirme" in message or "Digite 1 para confirmar" in message:
        print("\n6. Confirmando dados da transferência (1)...")
        response = send_webhook_message(PHONE_NUMBER, "1")
        print(f"Status: {response.status_code}")
        message, state = wait_and_check_response(PHONE_NUMBER, "Confirmação")
    
    print("\n=== TESTE COMPLETO CONCLUÍDO ===")
    print(f"Estado final: {state}")
    print(f"Mensagem final: {message}")

if __name__ == "__main__":
    test_complete_beneficiary_flow()