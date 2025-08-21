import logging
import traceback
from typing import Dict, Any, Optional, Tuple
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from enum import Enum
import json

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Níveis de severidade dos erros"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Categorias de erros"""
    WHATSAPP_API = "whatsapp_api"
    PAYMENT_API = "payment_api"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    SYSTEM = "system"
    USER_INPUT = "user_input"

class ErrorHandler:
    """
    Sistema centralizado de tratamento de erros
    """
    
    def __init__(self):
        self.error_counts = {}
        self.last_notification = {}
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None, 
                    category: ErrorCategory = ErrorCategory.SYSTEM,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    user_phone: str = None) -> Tuple[str, bool]:
        """
        Processa um erro e retorna mensagem para o usuário
        
        Args:
            error: Exceção capturada
            context: Contexto adicional do erro
            category: Categoria do erro
            severity: Severidade do erro
            user_phone: Telefone do usuário (se aplicável)
            
        Returns:
            Tuple[mensagem_usuario, deve_notificar_admin]
        """
        error_id = self._generate_error_id()
        error_details = self._extract_error_details(error, context)
        
        # Log do erro
        self._log_error(error_id, error_details, category, severity, user_phone)
        
        # Incrementa contador de erros
        self._increment_error_count(category, severity)
        
        # Determina se deve notificar administradores
        should_notify = self._should_notify_admin(category, severity)
        
        # Envia notificação se necessário
        if should_notify:
            self._notify_administrators(error_id, error_details, category, severity)
        
        # Retorna mensagem apropriada para o usuário
        user_message = self._get_user_message(category, severity, error_id)
        
        return user_message, should_notify
    
    def _generate_error_id(self) -> str:
        """Gera ID único para o erro"""
        import uuid
        return f"ERR_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    def _extract_error_details(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extrai detalhes do erro"""
        return {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {},
            "timestamp": timezone.now().isoformat()
        }
    
    def _log_error(self, error_id: str, error_details: Dict[str, Any], 
                  category: ErrorCategory, severity: ErrorSeverity, user_phone: str = None):
        """Registra o erro nos logs"""
        log_data = {
            "error_id": error_id,
            "category": category.value,
            "severity": severity.value,
            "user_phone": user_phone,
            **error_details
        }
        
        log_message = f"[{error_id}] {category.value.upper()} ERROR: {error_details['error_message']}"
        
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            logger.error(log_message, extra=log_data)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, extra=log_data)
        else:
            logger.info(log_message, extra=log_data)
    
    def _increment_error_count(self, category: ErrorCategory, severity: ErrorSeverity):
        """Incrementa contador de erros"""
        key = f"{category.value}_{severity.value}"
        current_hour = timezone.now().strftime('%Y%m%d_%H')
        
        if key not in self.error_counts:
            self.error_counts[key] = {}
        
        if current_hour not in self.error_counts[key]:
            self.error_counts[key][current_hour] = 0
        
        self.error_counts[key][current_hour] += 1
    
    def _should_notify_admin(self, category: ErrorCategory, severity: ErrorSeverity) -> bool:
        """Determina se deve notificar administradores"""
        # Sempre notifica erros críticos
        if severity == ErrorSeverity.CRITICAL:
            return True
        
        # Notifica erros de alta severidade em APIs críticas
        if severity == ErrorSeverity.HIGH and category in [
            ErrorCategory.WHATSAPP_API, 
            ErrorCategory.PAYMENT_API,
            ErrorCategory.DATABASE
        ]:
            return True
        
        # Verifica se há muitos erros da mesma categoria
        key = f"{category.value}_{severity.value}"
        current_hour = timezone.now().strftime('%Y%m%d_%H')
        
        if key in self.error_counts and current_hour in self.error_counts[key]:
            count = self.error_counts[key][current_hour]
            
            # Thresholds por severidade
            thresholds = {
                ErrorSeverity.HIGH: 5,
                ErrorSeverity.MEDIUM: 10,
                ErrorSeverity.LOW: 20
            }
            
            if count >= thresholds.get(severity, 10):
                # Evita spam de notificações
                last_notification_key = f"{key}_{current_hour}"
                if last_notification_key not in self.last_notification:
                    self.last_notification[last_notification_key] = timezone.now()
                    return True
        
        return False
    
    def _notify_administrators(self, error_id: str, error_details: Dict[str, Any], 
                             category: ErrorCategory, severity: ErrorSeverity):
        """Notifica administradores sobre o erro"""
        try:
            subject = f"[{severity.value.upper()}] Erro no Sistema WhatsApp - {error_id}"
            
            message = f"""
            ERRO DETECTADO NO SISTEMA
            
            ID do Erro: {error_id}
            Categoria: {category.value}
            Severidade: {severity.value}
            Timestamp: {error_details['timestamp']}
            
            Tipo do Erro: {error_details['error_type']}
            Mensagem: {error_details['error_message']}
            
            Contexto:
            {json.dumps(error_details['context'], indent=2, ensure_ascii=False)}
            
            Traceback:
            {error_details['traceback']}
            
            ---
            Sistema de Monitoramento WhatsApp
            """
            
            # Lista de administradores (configurável)
            admin_emails = getattr(settings, 'ADMIN_NOTIFICATION_EMAILS', [])
            
            if admin_emails:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=admin_emails,
                    fail_silently=True
                )
                
                logger.info(f"Notificação de erro {error_id} enviada para administradores")
            
        except Exception as e:
            logger.error(f"Falha ao enviar notificação de erro: {str(e)}")
    
    def _get_user_message(self, category: ErrorCategory, severity: ErrorSeverity, error_id: str) -> str:
        """Retorna mensagem apropriada para o usuário"""
        from .message_templates import message_templates
        
        # Mensagens específicas por categoria
        category_messages = {
            ErrorCategory.WHATSAPP_API: "Problema temporário com o WhatsApp. Tente novamente em alguns instantes.",
            ErrorCategory.PAYMENT_API: "Problema temporário com o sistema de pagamentos. Tente novamente mais tarde.",
            ErrorCategory.DATABASE: "Sistema temporariamente indisponível. Tente novamente em alguns minutos.",
            ErrorCategory.EXTERNAL_API: "Serviço externo indisponível. Tente novamente mais tarde.",
            ErrorCategory.VALIDATION: "Dados inválidos. Verifique as informações e tente novamente.",
            ErrorCategory.AUTHENTICATION: "Problema de autenticação. Entre em contato com o suporte.",
            ErrorCategory.RATE_LIMIT: "Muitas tentativas. Aguarde alguns minutos antes de tentar novamente.",
            ErrorCategory.NETWORK: "Problema de conexão. Tente novamente em alguns instantes.",
            ErrorCategory.USER_INPUT: "Formato inválido. Verifique sua mensagem e tente novamente."
        }
        
        base_message = category_messages.get(category, "Erro temporário no sistema.")
        
        # Adiciona ID do erro para erros críticos
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            base_message += f"\n\n🆔 Código do erro: {error_id}"
            base_message += "\n\nSe o problema persistir, entre em contato com nosso suporte informando este código."
        
        return base_message
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas de erros"""
        current_hour = timezone.now().strftime('%Y%m%d_%H')
        
        stats = {
            "current_hour": current_hour,
            "error_counts": {},
            "total_errors": 0
        }
        
        for key, hours_data in self.error_counts.items():
            if current_hour in hours_data:
                stats["error_counts"][key] = hours_data[current_hour]
                stats["total_errors"] += hours_data[current_hour]
        
        return stats
    
    def clear_old_error_counts(self, hours_to_keep: int = 24):
        """Remove contadores de erros antigos"""
        current_time = timezone.now()
        cutoff_time = current_time - timezone.timedelta(hours=hours_to_keep)
        
        for category_key in list(self.error_counts.keys()):
            hours_to_remove = []
            
            for hour_key in self.error_counts[category_key]:
                try:
                    hour_time = timezone.datetime.strptime(hour_key, '%Y%m%d_%H')
                    hour_time = timezone.make_aware(hour_time)
                    
                    if hour_time < cutoff_time:
                        hours_to_remove.append(hour_key)
                except ValueError:
                    # Remove chaves com formato inválido
                    hours_to_remove.append(hour_key)
            
            for hour_key in hours_to_remove:
                del self.error_counts[category_key][hour_key]
            
            # Remove categoria se não há mais dados
            if not self.error_counts[category_key]:
                del self.error_counts[category_key]

class WhatsAppErrorHandler(ErrorHandler):
    """Handler específico para erros do WhatsApp"""
    
    def handle_whatsapp_error(self, error: Exception, phone: str = None, 
                             message_data: Dict[str, Any] = None) -> str:
        """Trata erros específicos do WhatsApp"""
        context = {
            "phone": phone,
            "message_data": message_data
        }
        
        # Determina severidade baseada no tipo de erro
        severity = ErrorSeverity.MEDIUM
        
        if "rate limit" in str(error).lower():
            severity = ErrorSeverity.HIGH
            category = ErrorCategory.RATE_LIMIT
        elif "authentication" in str(error).lower() or "token" in str(error).lower():
            severity = ErrorSeverity.CRITICAL
            category = ErrorCategory.AUTHENTICATION
        elif "network" in str(error).lower() or "connection" in str(error).lower():
            severity = ErrorSeverity.MEDIUM
            category = ErrorCategory.NETWORK
        else:
            category = ErrorCategory.WHATSAPP_API
        
        user_message, _ = self.handle_error(
            error=error,
            context=context,
            category=category,
            severity=severity,
            user_phone=phone
        )
        
        return user_message

class PaymentErrorHandler(ErrorHandler):
    """Handler específico para erros de pagamento"""
    
    def handle_payment_error(self, error: Exception, payment_data: Dict[str, Any] = None) -> str:
        """Trata erros específicos de pagamento"""
        context = {
            "payment_data": payment_data
        }
        
        severity = ErrorSeverity.HIGH  # Erros de pagamento são sempre de alta prioridade
        
        user_message, _ = self.handle_error(
            error=error,
            context=context,
            category=ErrorCategory.PAYMENT_API,
            severity=severity
        )
        
        return user_message

# Instâncias globais dos handlers
error_handler = ErrorHandler()
whatsapp_error_handler = WhatsAppErrorHandler()
payment_error_handler = PaymentErrorHandler()