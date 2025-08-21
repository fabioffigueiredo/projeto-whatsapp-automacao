#!/usr/bin/env python3
"""
Script para monitorar mensagens recebidas no webhook em tempo real
"""

import time
import os
from datetime import datetime
import subprocess

def monitor_webhook_messages():
    """Monitora mensagens recebidas no webhook em tempo real"""
    
    print("🔍 Monitor de Mensagens WhatsApp - Webhook")
    print("="*50)
    print("📱 Aguardando mensagens...")
    print("💡 Envie uma mensagem para o número WhatsApp para testar")
    print("⏹️ Pressione Ctrl+C para parar\n")
    
    log_file = "backend/logs/django.log"
    
    if not os.path.exists(log_file):
        print(f"❌ Arquivo de log não encontrado: {log_file}")
        return
    
    # Obter tamanho inicial do arquivo
    try:
        with open(log_file, 'rb') as f:
            f.seek(0, 2)  # Ir para o final do arquivo
            initial_size = f.tell()
    except Exception as e:
        print(f"❌ Erro ao acessar arquivo de log: {e}")
        return
    
    print(f"📋 Monitorando: {log_file}")
    print(f"📊 Tamanho inicial: {initial_size} bytes\n")
    
    try:
        while True:
            try:
                # Verificar se o arquivo cresceu
                current_size = os.path.getsize(log_file)
                
                if current_size > initial_size:
                    # Ler novas linhas
                    with open(log_file, 'rb') as f:
                        f.seek(initial_size)
                        new_content = f.read().decode('utf-8', errors='ignore')
                    
                    if new_content.strip():
                        lines = new_content.strip().split('\n')
                        
                        for line in lines:
                            if line.strip():
                                timestamp = datetime.now().strftime("%H:%M:%S")
                                
                                # Destacar mensagens importantes
                                if any(keyword in line.lower() for keyword in ['webhook', 'whatsapp', 'message', 'post']):
                                    if 'error' in line.lower() or 'warning' in line.lower():
                                        print(f"⚠️ [{timestamp}] {line}")
                                    elif 'info' in line.lower() or '200' in line:
                                        print(f"✅ [{timestamp}] {line}")
                                    else:
                                        print(f"📝 [{timestamp}] {line}")
                                else:
                                    print(f"📄 [{timestamp}] {line}")
                    
                    initial_size = current_size
                
                time.sleep(1)  # Verificar a cada segundo
                
            except FileNotFoundError:
                print(f"❌ Arquivo de log removido: {log_file}")
                break
            except Exception as e:
                print(f"❌ Erro ao monitorar: {e}")
                time.sleep(2)
                
    except KeyboardInterrupt:
        print("\n\n⏹️ Monitoramento interrompido pelo usuário")
        print("\n📋 Resumo do teste:")
        print("   1. Se você viu mensagens com ✅, o webhook está funcionando")
        print("   2. Se você viu ⚠️ com 'Invalid signature', é normal (validação de assinatura)")
        print("   3. Se não viu nenhuma mensagem, verifique:")
        print("      - Se o número está na lista permitida do Facebook")
        print("      - Se o webhook URL está correto no Facebook")
        print("      - Se o Django está rodando na porta 8001")

def show_recent_logs():
    """Mostra logs recentes antes de iniciar o monitoramento"""
    
    print("📋 Últimas 5 entradas do log:")
    print("-" * 40)
    
    try:
        result = subprocess.run(
            ['powershell', '-Command', 'Get-Content .\\backend\\logs\\django.log | Select-Object -Last 5'],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    print(f"   {line}")
        else:
            print("   (Nenhum log recente encontrado)")
            
    except Exception as e:
        print(f"   ❌ Erro ao ler logs: {e}")
    
    print("-" * 40)
    print()

if __name__ == "__main__":
    print("🚀 Iniciando monitor de webhook...\n")
    
    # Mostrar logs recentes primeiro
    show_recent_logs()
    
    # Iniciar monitoramento
    monitor_webhook_messages()