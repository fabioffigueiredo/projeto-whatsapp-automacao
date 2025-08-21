#!/usr/bin/env python
"""
Teste de validação completa do sistema
Verifica se todas as funcionalidades estão operando corretamente
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

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
            return 'ERRO', 'ERRO'
    except Exception as e:
        return 'ERRO', 'ERRO'

def test_scenario(phone_number, scenario_name, messages):
    """Testa um cenário específico"""
    print(f"\n=== TESTANDO: {scenario_name} ===")
    print(f"Número: {phone_number}")
    
    results = []
    
    for i, message in enumerate(messages, 1):
        print(f"\n{i}. Enviando: '{message}'")
        response = send_webhook_message(phone_number, message)
        
        if response.status_code != 200:
            print(f"   ❌ ERRO: Status {response.status_code}")
            results.append(False)
            continue
        
        time.sleep(1)
        reply, state = get_last_response(phone_number)
        
        if reply == 'ERRO':
            print(f"   ❌ ERRO: Não foi possível obter resposta")
            results.append(False)
        else:
            print(f"   ✅ Resposta: {reply[:100]}...")
            print(f"   📍 Estado: {state}")
            results.append(True)
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 Taxa de sucesso: {success_rate:.1f}% ({sum(results)}/{len(results)})")
    return success_rate

def validate_system():
    """Executa validação completa do sistema"""
    print("🚀 INICIANDO VALIDAÇÃO COMPLETA DO SISTEMA")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "Novo Cliente - Cadastro Completo",
            "phone": "5511111111111",
            "messages": [
                "oi",
                "João Silva",
                "joao123",
                "11122233344",
                "1",
                "joao@email.com",
                "Rua A, 123, São Paulo, SP",
                "100",
                "1"
            ]
        },
        {
            "name": "Cliente Existente - Login",
            "phone": "5511222222222",
            "messages": [
                "oi",
                "1",
                "usuario123",
                "senha123",
                "11122233344",
                "1",
                "maria@email.com",
                "Rua B, 456, Rio de Janeiro, RJ",
                "200",
                "1"
            ]
        },
        {
            "name": "Validação de CPF Inválido",
            "phone": "5511333333333",
            "messages": [
                "oi",
                "Maria Santos",
                "maria456",
                "123",  # CPF inválido
                "12345678901",  # CPF válido
                "1",
                "maria@test.com",
                "Rua C, 789, Belo Horizonte, MG",
                "50",
                "1"
            ]
        },
        {
            "name": "Alteração de Dados",
            "phone": "5511444444444",
            "messages": [
                "oi",
                "Pedro Costa",
                "pedro789",
                "98765432100",
                "1",
                "pedro@email.com",
                "Rua D, 321, Salvador, BA",
                "75",
                "2",  # Alterar dados
                "4",  # Alterar valor
                "150",  # Novo valor
                "1"   # Confirmar
            ]
        }
    ]
    
    total_success = []
    
    for scenario in scenarios:
        success_rate = test_scenario(
            scenario["phone"],
            scenario["name"],
            scenario["messages"]
        )
        total_success.append(success_rate)
        time.sleep(2)  # Pausa entre cenários
    
    # Resumo final
    print("\n" + "=" * 50)
    print("📋 RESUMO DA VALIDAÇÃO")
    print("=" * 50)
    
    overall_success = sum(total_success) / len(total_success)
    
    for i, scenario in enumerate(scenarios):
        status = "✅" if total_success[i] >= 80 else "⚠️" if total_success[i] >= 60 else "❌"
        print(f"{status} {scenario['name']}: {total_success[i]:.1f}%")
    
    print(f"\n🎯 TAXA GERAL DE SUCESSO: {overall_success:.1f}%")
    
    if overall_success >= 90:
        print("🎉 SISTEMA VALIDADO COM SUCESSO!")
    elif overall_success >= 70:
        print("⚠️ SISTEMA FUNCIONAL COM ALGUMAS MELHORIAS NECESSÁRIAS")
    else:
        print("❌ SISTEMA PRECISA DE CORREÇÕES IMPORTANTES")
    
    return overall_success

if __name__ == "__main__":
    validate_system()