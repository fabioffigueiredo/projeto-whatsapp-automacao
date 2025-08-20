import requests
import logging
from django.conf import settings
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class WhatsAppCloudAPI:
    """
    Serviço para integração com WhatsApp Cloud API
    Documentação: https://developers.facebook.com/docs/whatsapp/cloud-api
    """
    
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v18.0"
        self.phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', None)
        self.access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', None)
        
        if not self.phone_number_id or not self.access_token:
            logger.warning("WhatsApp credentials not configured. Using mock mode.")
    
    def send_message(self, to: str, message: str) -> Dict[str, Any]:
        """
        Envia mensagem de texto via WhatsApp Cloud API
        
        Args:
            to: Número do destinatário (formato: 5511999999999)
            message: Texto da mensagem
            
        Returns:
            Dict com resposta da API ou mock
        """
        if not self._is_configured():
            return self._mock_send_response(to, message)
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Message sent to {to}: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send WhatsApp message to {to}: {e}")
            return {"error": str(e), "success": False}
    
    def send_template_message(self, to: str, template_name: str, 
                            language_code: str = "pt_BR", 
                            components: Optional[list] = None) -> Dict[str, Any]:
        """
        Envia mensagem template via WhatsApp Cloud API
        
        Args:
            to: Número do destinatário
            template_name: Nome do template aprovado
            language_code: Código do idioma (pt_BR, en_US, etc.)
            components: Componentes do template (parâmetros)
            
        Returns:
            Dict com resposta da API
        """
        if not self._is_configured():
            return self._mock_send_response(to, f"Template: {template_name}")
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code}
            }
        }
        
        if components:
            payload["template"]["components"] = components
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Template message sent to {to}: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send WhatsApp template to {to}: {e}")
            return {"error": str(e), "success": False}
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verifica webhook do WhatsApp Cloud API
        
        Args:
            mode: Modo de verificação
            token: Token de verificação
            challenge: Challenge string
            
        Returns:
            Challenge string se válido, None caso contrário
        """
        verify_token = getattr(settings, 'WHATSAPP_VERIFY_TOKEN', 'default_verify_token')
        
        if mode == "subscribe" and token == verify_token:
            logger.info("WhatsApp webhook verified successfully")
            return challenge
        
        logger.warning(f"WhatsApp webhook verification failed. Mode: {mode}, Token: {token}")
        return None
    
    def parse_webhook_message(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Extrai dados da mensagem do webhook do WhatsApp
        
        Args:
            webhook_data: Dados do webhook
            
        Returns:
            Dict com phone e message ou None se inválido
        """
        try:
            entry = webhook_data.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})
            
            messages = value.get("messages", [])
            if not messages:
                return None
            
            message = messages[0]
            phone = message.get("from")
            text = message.get("text", {}).get("body", "")
            
            if phone and text:
                return {"phone": phone, "message": text}
            
        except (IndexError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse WhatsApp webhook: {e}")
        
        return None
    
    def _is_configured(self) -> bool:
        """Verifica se as credenciais estão configuradas"""
        return bool(self.phone_number_id and self.access_token)
    
    def _mock_send_response(self, to: str, message: str) -> Dict[str, Any]:
        """Resposta mock para desenvolvimento"""
        logger.info(f"MOCK: Sending to {to}: {message}")
        return {
            "messaging_product": "whatsapp",
            "contacts": [{"input": to, "wa_id": to}],
            "messages": [{"id": f"mock_msg_{to}_{len(message)}"}],
            "mock": True
        }

# Instância global do serviço
whatsapp_service = WhatsAppCloudAPI()