#!/usr/bin/env python3
"""
Script para verificar e adicionar números à lista permitida do WhatsApp Business
"""

import requests
import json
import os
from datetime import datetime

def check_phone_whitelist():
    """Verifica se o número está na lista permitida"""
    
    print("📋 Verificação de Lista Permitida - WhatsApp Business")
    print("="*60)
    
    # Carregar configurações
    env_files = ['backend/.env', '.env']
    
    for env_file in env_files:
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
            break
        except FileNotFoundError:
            continue
    
    access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    app_id = os.getenv('WHATSAPP_APP_ID')
    business_account_id = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID')
    
    print(f"📱 App ID: {app_id}")
    print(f"🏢 Business Account ID: {business_account_id}")
    
    # Verificar números de teste permitidos
    print("\n1️⃣ Verificando números de teste permitidos...")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # Endpoint para verificar números de teste
    url = f"https://graph.facebook.com/v18.0/{app_id}/subscribed_apps"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"📊 Status da verificação: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ App subscrito: {data}")
        else:
            print(f"⚠️ Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Verificar configuração do webhook
    print("\n2️⃣ Verificando configuração do webhook...")
    
    webhook_url = f"https://graph.facebook.com/v18.0/{app_id}/subscriptions"
    
    try:
        response = requests.get(webhook_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            webhooks = response.json()
            print(f"✅ Webhooks configurados: {len(webhooks.get('data', []))}")
            
            for webhook in webhooks.get('data', []):
                print(f"   - Objeto: {webhook.get('object', 'N/A')}")
                print(f"   - Callback URL: {webhook.get('callback_url', 'N/A')}")
                print(f"   - Campos: {webhook.get('fields', [])}")
        else:
            print(f"⚠️ Erro ao verificar webhooks: {response.status_code}")
            print(f"   Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro ao verificar webhooks: {e}")
    
    # Instruções detalhadas
    print("\n3️⃣ Instruções para adicionar números à lista permitida:")
    print("\n🌐 Acesse o Facebook Developer Console:")
    print(f"   1. Vá para: https://developers.facebook.com/apps/{app_id}/whatsapp-business/wa-dev-console/")
    print("   2. Na seção 'Send and receive messages'")
    print("   3. Encontre 'To' field")
    print("   4. Adicione o número no formato: +5521964641561")
    print("   5. Clique em 'Add phone number'")
    
    print("\n📱 Números que devem estar na lista:")
    test_numbers = [
        "+5521964641561",  # Número do teste
        "+5511999999999",  # Exemplo adicional
    ]
    
    for number in test_numbers:
        print(f"   - {number}")
    
    print("\n⚠️ IMPORTANTE:")
    print("   • Números devem incluir código do país (+55 para Brasil)")
    print("   • Aguarde 5-10 minutos após adicionar para propagação")
    print("   • Máximo de 5 números na lista durante desenvolvimento")
    print("   • Para produção, não há limite de números")
    
    # Teste de envio após verificação
    print("\n4️⃣ Teste de envio (após adicionar à lista):")
    
    test_phone = input("\n📱 Digite o número para testar (formato: +5521999999999) ou ENTER para pular: ")
    
    if test_phone.strip():
        # Limpar e formatar número
        clean_phone = ''.join(filter(str.isdigit, test_phone))
        
        phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": "text",
            "text": {
                "body": f"✅ Teste após verificação da lista - {datetime.now().strftime('%H:%M:%S')}\n\nSe você recebeu esta mensagem, o número foi adicionado corretamente à lista permitida!"
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('messages', [{}])[0].get('id', 'N/A')
                print(f"\n✅ Mensagem enviada com sucesso!")
                print(f"   Message ID: {message_id}")
                print(f"   Para: {clean_phone}")
                print(f"\n📱 Verifique seu WhatsApp agora!")
            else:
                print(f"\n❌ Erro no envio: {response.status_code}")
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                print(f"   Detalhes: {error_data}")
                
                # Analisar erro específico
                if response.status_code == 400:
                    print("\n🔍 Possíveis causas do erro 400:")
                    print("   • Número não está na lista permitida")
                    print("   • Formato do número incorreto")
                    print("   • Token de acesso inválido")
                elif response.status_code == 403:
                    print("\n🔍 Erro 403 - Acesso negado:")
                    print("   • Verifique se o token tem permissões corretas")
                    print("   • Confirme se o app está aprovado para WhatsApp Business")
                    
        except Exception as e:
            print(f"\n❌ Erro de conexão: {e}")
    
    print("\n📋 Checklist final:")
    print("   □ Número adicionado no Facebook Developer Console")
    print("   □ Aguardou 5-10 minutos para propagação")
    print("   □ Número inclui código do país (+55)")
    print("   □ WhatsApp instalado no número de destino")
    print("   □ Número não bloqueou mensagens comerciais")
    
    print("\n🔄 Se ainda não funcionar:")
    print("   1. Remova e adicione o número novamente")
    print("   2. Aguarde mais tempo (até 30 minutos)")
    print("   3. Teste com outro número")
    print("   4. Verifique se a conta WhatsApp Business não foi suspensa")

if __name__ == "__main__":
    check_phone_whitelist()