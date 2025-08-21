import requests
import json
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

class WhatsAppBusinessService:
    """
    Serviço para integração com WhatsApp Business API
    """
    
    def __init__(self):
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.business_account_id = settings.WHATSAPP_BUSINESS_ACCOUNT_ID
        self.app_id = settings.WHATSAPP_APP_ID
        self.app_secret = settings.WHATSAPP_APP_SECRET
        self.base_url = settings.WHATSAPP_BASE_URL
        self.verify_token = settings.WHATSAPP_VERIFY_TOKEN
        
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Valida se todas as configurações necessárias estão presentes"""
        required_settings = [
            ('WHATSAPP_ACCESS_TOKEN', self.access_token),
            ('WHATSAPP_PHONE_NUMBER_ID', self.phone_number_id),
        ]
        
        missing_settings = [name for name, value in required_settings if not value]
        
        if missing_settings:
            raise ImproperlyConfigured(
                f"As seguintes configurações do WhatsApp são obrigatórias: {', '.join(missing_settings)}"
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """Retorna os headers padrão para requisições à API"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def send_text_message(self, to: str, message: str) -> Dict[str, Any]:
        """
        Envia uma mensagem de texto
        
        Args:
            to: Número do destinatário (formato: 5511999999999)
            message: Texto da mensagem
            
        Returns:
            Dict com a resposta da API
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Mensagem enviada com sucesso para {to}: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar mensagem para {to}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Resposta da API: {e.response.text}")
            raise
    
    def send_template_message(self, to: str, template_name: str, language_code: str = "pt_BR", 
                            components: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Envia uma mensagem usando template aprovado
        
        Args:
            to: Número do destinatário
            template_name: Nome do template aprovado
            language_code: Código do idioma (padrão: pt_BR)
            components: Componentes do template (parâmetros, botões, etc.)
            
        Returns:
            Dict com a resposta da API
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        if components:
            payload["template"]["components"] = components
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Template {template_name} enviado com sucesso para {to}: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar template {template_name} para {to}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Resposta da API: {e.response.text}")
            raise
    
    def send_interactive_message(self, to: str, interactive_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envia uma mensagem interativa (botões, lista, etc.)
        
        Args:
            to: Número do destinatário
            interactive_data: Dados da mensagem interativa
            
        Returns:
            Dict com a resposta da API
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": interactive_data
        }
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Mensagem interativa enviada com sucesso para {to}: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar mensagem interativa para {to}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Resposta da API: {e.response.text}")
            raise
    
    def mark_message_as_read(self, message_id: str) -> Dict[str, Any]:
        """
        Marca uma mensagem como lida
        
        Args:
            message_id: ID da mensagem
            
        Returns:
            Dict com a resposta da API
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Mensagem {message_id} marcada como lida: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao marcar mensagem {message_id} como lida: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Resposta da API: {e.response.text}")
            raise
    
    def get_media_url(self, media_id: str) -> str:
        """
        Obtém a URL de um arquivo de mídia
        
        Args:
            media_id: ID do arquivo de mídia
            
        Returns:
            URL do arquivo
        """
        url = f"{self.base_url}/{media_id}"
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            media_url = result.get('url')
            
            if not media_url:
                raise ValueError(f"URL não encontrada para mídia {media_id}")
            
            logger.info(f"URL obtida para mídia {media_id}: {media_url}")
            return media_url
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao obter URL da mídia {media_id}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Resposta da API: {e.response.text}")
            raise
    
    def download_media(self, media_url: str) -> bytes:
        """
        Baixa um arquivo de mídia
        
        Args:
            media_url: URL do arquivo
            
        Returns:
            Conteúdo do arquivo em bytes
        """
        try:
            response = requests.get(
                media_url,
                headers=self._get_headers(),
                timeout=60
            )
            response.raise_for_status()
            
            logger.info(f"Mídia baixada com sucesso: {len(response.content)} bytes")
            return response.content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao baixar mídia {media_url}: {str(e)}")
            raise
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verifica o webhook do WhatsApp
        
        Args:
            mode: Modo de verificação
            token: Token de verificação
            challenge: Challenge string
            
        Returns:
            Challenge string se válido, None caso contrário
        """
        if mode == "subscribe" and token == self.verify_token:
            logger.info("Webhook verificado com sucesso")
            return challenge
        
        logger.warning(f"Falha na verificação do webhook: mode={mode}, token={token}")
        return None
    
    def validate_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Valida a assinatura do webhook (para produção)
        
        Args:
            payload: Payload da requisição
            signature: Assinatura do header X-Hub-Signature-256
            
        Returns:
            True se válida, False caso contrário
        """
        import hmac
        import hashlib
        
        if not self.app_secret:
            logger.warning("App secret não configurado, pulando validação de assinatura")
            return True
        
        try:
            # Remove o prefixo 'sha256=' se presente
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            # Calcula a assinatura esperada
            expected_signature = hmac.new(
                self.app_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compara as assinaturas
            is_valid = hmac.compare_digest(signature, expected_signature)
            
            if not is_valid:
                logger.warning("Assinatura do webhook inválida")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Erro ao validar assinatura do webhook: {str(e)}")
            return False
    
    def get_business_profile(self) -> Dict[str, Any]:
        """
        Obtém o perfil do negócio
        
        Returns:
            Dict com informações do perfil
        """
        url = f"{self.base_url}/{self.phone_number_id}/whatsapp_business_profile"
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Perfil do negócio obtido: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao obter perfil do negócio: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Resposta da API: {e.response.text}")
            raise

# Instância global do serviço
whatsapp_service = WhatsAppBusinessService()