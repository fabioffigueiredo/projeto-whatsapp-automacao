from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
import logging

from ..models import Client
from ..authentication import ClientAuthService, ClientTokenAuthentication
from ..serializers import ClientLoginSerializer, ClientRegistrationSerializer, ClientProfileSerializer

logger = logging.getLogger(__name__)

@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def client_login(request):
    """
    Endpoint para login de clientes
    """
    try:
        serializer = ClientLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username_or_email = serializer.validated_data['username_or_email']
        password = serializer.validated_data['password']
        
        # Autentica cliente
        auth_result = ClientAuthService.authenticate_client(username_or_email, password)
        
        if not auth_result:
            return Response({
                "error": "Credenciais inválidas",
                "message": "Nome de usuário/email ou senha incorretos"
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        client, token = auth_result
        
        return Response({
            "success": True,
            "token": token,
            "client": {
                "id": client.id,
                "name": client.name,
                "username": client.username,
                "email": client.email,
                "phone": client.phone,
                "registration_completed": client.registration_completed
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in client login: {e}")
        return Response({
            "error": "Erro interno",
            "message": "Tente novamente mais tarde"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def client_register(request):
    """
    Endpoint para registro inicial de clientes (via WhatsApp)
    """
    try:
        serializer = ClientRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        name = serializer.validated_data['name']
        phone = serializer.validated_data['phone']
        username = serializer.validated_data['username']
        email = serializer.validated_data.get('email')
        
        # Registra cliente
        client = ClientAuthService.register_client(name, phone, username, email)
        
        return Response({
            "success": True,
            "message": "Cliente registrado com sucesso",
            "client": {
                "id": client.id,
                "name": client.name,
                "username": client.username,
                "phone": client.phone,
                "registration_completed": client.registration_completed
            }
        }, status=status.HTTP_201_CREATED)
        
    except ValueError as e:
        return Response({
            "error": "Dados inválidos",
            "message": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error in client registration: {e}")
        return Response({
            "error": "Erro interno",
            "message": "Tente novamente mais tarde"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def complete_registration(request):
    """
    Endpoint para completar registro do cliente (email + senha)
    """
    try:
        client_id = request.data.get('client_id')
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not all([client_id, email, password]):
            return Response({
                "error": "Dados obrigatórios",
                "message": "client_id, email e password são obrigatórios"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({
                "error": "Cliente não encontrado",
                "message": "ID do cliente inválido"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verifica se email já está em uso
        if Client.objects.filter(email=email).exclude(id=client_id).exists():
            return Response({
                "error": "Email já cadastrado",
                "message": "Este email já está sendo usado por outro cliente"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Completa o registro
        ClientAuthService.complete_registration(client, email, password)
        
        # Gera token para login automático
        token = ClientAuthService.generate_token(client)
        
        return Response({
            "success": True,
            "message": "Registro completado com sucesso",
            "token": token,
            "client": {
                "id": client.id,
                "name": client.name,
                "username": client.username,
                "email": client.email,
                "phone": client.phone,
                "registration_completed": client.registration_completed
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error completing registration: {e}")
        return Response({
            "error": "Erro interno",
            "message": "Tente novamente mais tarde"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET", "PUT"])
def client_profile(request):
    """
    Endpoint para visualizar e atualizar perfil do cliente
    Requer autenticação
    """
    # Usa autenticação customizada
    auth = ClientTokenAuthentication()
    auth_result = auth.authenticate(request)
    
    if not auth_result:
        return Response({
            "error": "Não autorizado",
            "message": "Token de acesso necessário"
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    client, token = auth_result
    
    if request.method == "GET":
        return Response({
            "client": {
                "id": client.id,
                "name": client.name,
                "username": client.username,
                "email": client.email,
                "phone": client.phone,
                "registration_completed": client.registration_completed,
                "created_at": client.created_at,
                "updated_at": client.updated_at
            }
        }, status=status.HTTP_200_OK)
    
    elif request.method == "PUT":
        try:
            serializer = ClientProfileSerializer(client, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response({
                "success": True,
                "message": "Perfil atualizado com sucesso",
                "client": {
                    "id": client.id,
                    "name": client.name,
                    "username": client.username,
                    "email": client.email,
                    "phone": client.phone,
                    "registration_completed": client.registration_completed
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error updating client profile: {e}")
            return Response({
                "error": "Erro interno",
                "message": "Tente novamente mais tarde"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
def change_password(request):
    """
    Endpoint para alterar senha do cliente
    """
    # Usa autenticação customizada
    auth = ClientTokenAuthentication()
    auth_result = auth.authenticate(request)
    
    if not auth_result:
        return Response({
            "error": "Não autorizado",
            "message": "Token de acesso necessário"
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    client, token = auth_result
    
    try:
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        
        if not all([current_password, new_password]):
            return Response({
                "error": "Dados obrigatórios",
                "message": "current_password e new_password são obrigatórios"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verifica senha atual
        if not ClientAuthService.verify_password(current_password, client.password_hash):
            return Response({
                "error": "Senha incorreta",
                "message": "Senha atual está incorreta"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Define nova senha
        ClientAuthService.set_password(client, new_password)
        
        return Response({
            "success": True,
            "message": "Senha alterada com sucesso"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        return Response({
            "error": "Erro interno",
            "message": "Tente novamente mais tarde"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)