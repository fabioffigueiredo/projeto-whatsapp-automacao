#!/usr/bin/env python
"""
Teste do fluxo completo começando do zero
Reinicia a conversa e testa todo o processo
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api"
PHONE_NUMBER = "5511888888888"  # Usar um número diferente

def clear_conversation(phone_number):
    """Simula limpeza da conversa usando um número diferente"""
    print(f"Usando número limpo para teste: {phone_number}")

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
    print(f"  {step_name} - Resposta: {message}")
    print(f"  {step_name} - Estado: {state}")
    return message, state

def test_fresh_flow():
    """Testa o fluxo completo começando do zero"""
    print("=== TESTE DO FLUXO COMPLETO DESDE O INÍCIO ===")
    
    # Limpar conversa anterior
    print("\n0. Limpando conversa anterior...")
    clear_conversation(PHONE_NUMBER)
    
    # 1. Iniciar conversa
    print("\n1. Iniciando conversa com 'oi'...")
    response = send_webhook_message(PHONE_NUMBER, "oi")
    print(f"Status: {response.status_code}")
    message, state = wait_and_check_response(PHONE_NUMBER, "Início")
    
    # 2. Responder que é cliente existente
    if "Como posso ajudá-lo" in message or "Bem-vindo" in message:
        print("\n2. Respondendo que sou cliente existente (1)...")
        response = send_webhook_message(PHONE_NUMBER, "1")
        print(f"Status: {response.status_code}")
        message, state = wait_and_check_response(PHONE_NUMBER, "Cliente")
    
    # 3. Fazer login (simular)
    if "login" in message.lower() or "senha" in message.lower():
        print("\n3. Fazendo login (usuario123)...")
        response = send_webhook_message(PHONE_NUMBER, "usuario123")
        print(f"Status: {response.status_code}")
        message, state = wait_and_check_response(PHONE_NUMBER, "Login")
        
        # Senha
        if "senha" in message.lower():
            print("\n3.1. Inserindo senha (senha123)...")
            response = send_webhook_message(PHONE_NUMBER, "senha123")
            print(f"Status: {response.status_code}")
            message, state = wait_and_check_response(PHONE_NUMBER, "Senha")
    
    # 4. Inserir CPF do beneficiário
    if "CPF" in message:
        print("\n4. Inserindo CPF do beneficiário (11122233344)...")
        response = send_webhook_message(PHONE_NUMBER, "11122233344")
        print(f"Status: {response.status_code}")
        message, state = wait_and_check_response(PHONE_NUMBER, "CPF")
    
    # 5. Confirmar cadastro de novo beneficiário
    if "Digite 1 para cadastrar" in message:
        print("\n5. Confirmando cadastro de novo beneficiário (1)...")
        response = send_webhook_message(PHONE_NUMBER, "1")
        print(f"Status: {response.status_code}")
        message, state = wait_and_check_response(PHONE_NUMBER, "Cadastro")
    
    # 6. Inserir chave PIX
    if "chave PIX" in message:
        print("\n6. Inserindo chave PIX (joao@email.com)...")
        response = send_webhook_message(PHONE_NUMBER, "joao@email.com")
        print(f"Status: {response.status_code}")
        message, state = wait_and_check_response(PHONE_NUMBER, "PIX")
    
    # 7. Inserir endereço
    if "endereço" in message:
        print("\n7. Inserindo endereço (Rua das Flores, 123, São Paulo, SP)...")
        response = send_webhook_message(PHONE_NUMBER, "Rua das Flores, 123, São Paulo, SP")
        print(f"Status: {response.status_code}")
        message, state = wait_and_check_response(PHONE_NUMBER, "Endereço")
    
    # 8. Inserir valor
    if "valor" in message:
        print("\n8. Inserindo valor (100)...")
        response = send_webhook_message(PHONE_NUMBER, "100")
        print(f"Status: {response.status_code}")
        message, state = wait_and_check_response(PHONE_NUMBER, "Valor")
    
    # 9. Confirmar dados
    if "Confirme" in message or "Digite 1 para confirmar" in message:
        print("\n9. Confirmando dados da transferência (1)...")
        response = send_webhook_message(PHONE_NUMBER, "1")
        print(f"Status: {response.status_code}")
        message, state = wait_and_check_response(PHONE_NUMBER, "Confirmação")
    
    print("\n=== TESTE COMPLETO CONCLUÍDO ===")
    print(f"Estado final: {state}")
    print(f"Mensagem final: {message}")

if __name__ == "__main__":
    test_fresh_flow()