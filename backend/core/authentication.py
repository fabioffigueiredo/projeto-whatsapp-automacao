from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
import hashlib
import jwt
from django.conf import settings
from .models import Client

class ClientTokenAuthentication(BaseAuthentication):
    """
    Autenticação customizada para clientes usando JWT tokens
    """
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
            
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            client_id = payload.get('client_id')
            
            if not client_id:
                raise AuthenticationFailed('Token inválido')
                
            client = Client.objects.get(id=client_id)
            return (client, token)
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token expirado')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Token inválido')
        except Client.DoesNotExist:
            raise AuthenticationFailed('Cliente não encontrado')
    
    def authenticate_header(self, request):
        return 'Bearer'

class ClientAuthService:
    """
    Serviço para autenticação e gerenciamento de clientes
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Cria hash da senha usando SHA256
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verifica se a senha corresponde ao hash
        """
        return ClientAuthService.hash_password(password) == password_hash
    
    @staticmethod
    def generate_token(client: Client) -> str:
        """
        Gera JWT token para o cliente
        """
        payload = {
            'client_id': client.id,
            'username': client.username,
            'exp': timezone.now() + timezone.timedelta(days=7)  # Token válido por 7 dias
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    
    @staticmethod
    def authenticate_client(username_or_email: str, password: str) -> tuple[Client, str] | None:
        """
        Autentica cliente e retorna o cliente e token se válido
        """
        try:
            # Busca por username ou email
            if '@' in username_or_email:
                client = Client.objects.get(email=username_or_email)
            else:
                client = Client.objects.get(username=username_or_email)
            
            # Verifica senha
            if client.password_hash and ClientAuthService.verify_password(password, client.password_hash):
                token = ClientAuthService.generate_token(client)
                return client, token
                
        except Client.DoesNotExist:
            pass
            
        return None
    
    @staticmethod
    def register_client(name: str, phone: str, username: str, email: str = None) -> Client:
        """
        Registra um novo cliente
        """
        # Verifica se username já existe
        if Client.objects.filter(username=username).exists():
            raise ValueError("Nome de usuário já existe")
            
        # Verifica se telefone já existe
        if Client.objects.filter(phone=phone).exists():
            raise ValueError("Telefone já cadastrado")
            
        # Verifica se email já existe (se fornecido)
        if email and Client.objects.filter(email=email).exists():
            raise ValueError("Email já cadastrado")
        
        client = Client.objects.create(
            name=name,
            phone=phone,
            username=username,
            email=email,
            is_registered=True,
            registration_completed=False
        )
        
        return client
    
    @staticmethod
    def set_password(client: Client, password: str) -> None:
        """
        Define senha para o cliente
        """
        client.password_hash = ClientAuthService.hash_password(password)
        client.save()
    
    @staticmethod
    def complete_registration(client: Client, email: str, password: str) -> None:
        """
        Completa o registro do cliente com email e senha
        """
        client.email = email
        client.password_hash = ClientAuthService.hash_password(password)
        client.registration_completed = True
        client.save()

def jwt_required(view_func):
    """
    Decorador para exigir autenticação JWT em views
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth = ClientTokenAuthentication()
        try:
            user_auth_tuple = auth.authenticate(request)
            if user_auth_tuple is None:
                return Response({
                    'error': 'Token de autenticação necessário'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            request.client = user_auth_tuple[0]
            request.token = user_auth_tuple[1]
            return view_func(request, *args, **kwargs)
            
        except AuthenticationFailed as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    return wrapper