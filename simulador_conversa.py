#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulador Interativo de Conversa WhatsApp - XPS247
Permite simular uma conversa passo a passo seguindo o fluxo de transferência
"""

import requests
import json
import time
from datetime import datetime

class SimuladorConversaWhatsApp:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.webhook_url = f"{self.base_url}/api/webhook/"
        self.phone_number = "5511999999999"
        self.conversation_state = "inicio"
        
    def enviar_mensagem(self, mensagem):
        """Envia uma mensagem para o webhook do WhatsApp"""
        payload = {
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
                        "messages": [{
                            "from": self.phone_number,
                            "id": f"msg_{int(time.time())}",
                            "timestamp": str(int(time.time())),
                            "text": {
                                "body": mensagem
                            },
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload)
            return response.status_code == 200, response.json() if response.status_code == 200 else response.text
        except Exception as e:
            return False, str(e)
    
    def verificar_servidor(self):
        """Verifica se o servidor Django está rodando"""
        try:
            response = requests.get(f"{self.base_url}/admin/")
            return response.status_code in [200, 302]
        except:
            return False
    
    def mostrar_cabecalho(self):
        """Mostra o cabeçalho do simulador"""
        print("\n" + "="*60)
        print("🤖 SIMULADOR INTERATIVO - CONVERSA WHATSAPP XPS247")
        print("="*60)
        print("📱 Simule uma conversa real de transferência internacional")
        print("💬 Digite suas respostas como se estivesse no WhatsApp")
        print("🔄 Siga o fluxo completo de cadastro e transferência")
        print("="*60)
    
    def mostrar_fluxo_esperado(self):
        """Mostra o fluxo esperado da conversa"""
        print("\n📋 FLUXO ESPERADO DA CONVERSA:")
        print("1️⃣  Saudação inicial → Digite qualquer coisa para começar")
        print("2️⃣  Opção de cadastro → Digite '1' para se cadastrar")
        print("3️⃣  Nome completo → Digite seu nome")
        print("4️⃣  Username → Crie um nome de usuário")
        print("5️⃣  Cadastro no site → Digite 'Pronto' após finalizar")
        print("6️⃣  CPF → Digite um CPF válido (ex: 123.456.789-00)")
        print("7️⃣  Valor → Digite o valor em USD (ex: 1000)")
        print("8️⃣  Beneficiário → Digite nome do beneficiário")
        print("9️⃣  Confirmação → Digite '1' para confirmar")
        print("🔟 Pagamento → Finalize o processo")
        print("-"*60)
    
    def iniciar_simulacao(self):
        """Inicia a simulação interativa"""
        self.mostrar_cabecalho()
        
        # Verificar se o servidor está rodando
        print("🔍 Verificando servidor Django...")
        if not self.verificar_servidor():
            print("❌ Erro: Servidor Django não está rodando!")
            print("💡 Execute: python manage.py runserver (no diretório backend)")
            return
        
        print("✅ Servidor Django está rodando!")
        self.mostrar_fluxo_esperado()
        
        print("\n🚀 INICIANDO SIMULAÇÃO...")
        print("💡 Dica: Digite 'sair' a qualquer momento para encerrar")
        print("\n" + "-"*60)
        
        contador_mensagem = 1
        
        while True:
            try:
                # Solicitar entrada do usuário
                print(f"\n📱 Mensagem #{contador_mensagem}")
                mensagem = input("👤 Você: ").strip()
                
                # Verificar se quer sair
                if mensagem.lower() in ['sair', 'exit', 'quit']:
                    print("\n👋 Simulação encerrada!")
                    break
                
                if not mensagem:
                    print("⚠️  Digite uma mensagem válida")
                    continue
                
                # Mostrar timestamp
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"⏰ [{timestamp}] Enviando: '{mensagem}'")
                
                # Enviar mensagem
                sucesso, resposta = self.enviar_mensagem(mensagem)
                
                if sucesso:
                    print("✅ Mensagem enviada com sucesso!")
                    print(f"📊 Status: 200 OK")
                    
                    # Aguardar um pouco para o processamento
                    print("⏳ Aguardando resposta do sistema...")
                    time.sleep(2)
                    
                    print("🤖 Sistema processou sua mensagem")
                    print("💡 Verifique os logs do servidor para ver a resposta")
                    
                else:
                    print(f"❌ Erro ao enviar mensagem: {resposta}")
                
                contador_mensagem += 1
                
                # Perguntar se quer continuar
                print("\n" + "-"*40)
                continuar = input("🔄 Pressione ENTER para próxima mensagem (ou 'sair' para encerrar): ")
                if continuar.lower() in ['sair', 'exit', 'quit']:
                    print("\n👋 Simulação encerrada!")
                    break
                    
            except KeyboardInterrupt:
                print("\n\n👋 Simulação interrompida pelo usuário!")
                break
            except Exception as e:
                print(f"\n❌ Erro inesperado: {e}")
                break
    
    def mostrar_dicas(self):
        """Mostra dicas para a simulação"""
        print("\n💡 DICAS PARA A SIMULAÇÃO:")
        print("• Siga o fluxo na ordem apresentada")
        print("• Use respostas realistas (nomes, valores, etc.)")
        print("• Observe os logs do servidor para ver as respostas")
        print("• Para CPF, use formato: 123.456.789-00")
        print("• Para valores, use números: 1000, 500, etc.")
        print("• Para confirmações, use: 1 (sim) ou 2 (não)")
        print("-"*50)

def main():
    """Função principal"""
    simulador = SimuladorConversaWhatsApp()
    
    while True:
        print("\n🎯 SIMULADOR DE CONVERSA WHATSAPP - XPS247")
        print("1 - Iniciar simulação interativa")
        print("2 - Ver fluxo esperado")
        print("3 - Ver dicas")
        print("0 - Sair")
        
        opcao = input("\n👉 Escolha uma opção: ").strip()
        
        if opcao == "1":
            simulador.iniciar_simulacao()
        elif opcao == "2":
            simulador.mostrar_fluxo_esperado()
        elif opcao == "3":
            simulador.mostrar_dicas()
        elif opcao == "0":
            print("\n👋 Até logo!")
            break
        else:
            print("\n❌ Opção inválida!")

if __name__ == "__main__":
    main()