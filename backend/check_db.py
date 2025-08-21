#!/usr/bin/env python
"""
Script para verificar dados no banco
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Conversation, MessageLog, WebhookLog

def check_database():
    print("=== VERIFICAÇÃO DO BANCO DE DADOS ===")
    
    # Conversas
    conv_count = Conversation.objects.count()
    print(f"Total de conversas: {conv_count}")
    
    if conv_count > 0:
        last_conv = Conversation.objects.last()
        print(f"Última conversa: {last_conv.external_user_id} - Estado: {last_conv.state_node}")
        print(f"Contexto: {last_conv.context_data}")
    
    # Mensagens
    msg_count = MessageLog.objects.count()
    print(f"\nTotal de mensagens: {msg_count}")
    
    if msg_count > 0:
        print("\nÚltimas 3 mensagens:")
        for msg in MessageLog.objects.order_by('-created_at')[:3]:
            print(f"  - {msg.conversation.external_user_id} | {msg.direction} | {msg.payload} | {msg.created_at}")
    
    # Webhooks
    webhook_count = WebhookLog.objects.count()
    print(f"\nTotal de webhooks: {webhook_count}")
    
    if webhook_count > 0:
        print("\nÚltimos 3 webhooks:")
        for webhook in WebhookLog.objects.order_by('-received_at')[:3]:
            print(f"  - {webhook.source} | {webhook.status} | {webhook.received_at}")
            print(f"    Payload: {webhook.payload}")

if __name__ == "__main__":
    check_database()