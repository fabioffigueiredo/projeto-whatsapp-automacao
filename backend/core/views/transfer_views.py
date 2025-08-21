from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from decimal import Decimal
import logging

from ..models import Transfer, Client
from ..services.transfer_service import TransferService
from ..serializers import (
    TransferCreateSerializer,
    TransferCalculationSerializer,
    TransferDetailSerializer,
    TransferListSerializer,
    TransferStatusUpdateSerializer,
    TransferSummarySerializer,
    PaymentLinkSerializer
)
# Temporarily commented out due to JWT dependency
# from ..authentication import jwt_required

logger = logging.getLogger(__name__)


@api_view(['POST'])
# @jwt_required  # Temporarily commented due to JWT dependency
def calculate_transfer(request):
    """Calcula os valores de uma transferência sem criá-la"""
    try:
        serializer = TransferCalculationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        amount_usd = serializer.validated_data['amount_usd']
        
        transfer_service = TransferService()
        calculations = transfer_service.calculate_transfer_amounts(amount_usd)
        
        return Response({
            'success': True,
            'data': {
                'amount_usd': float(amount_usd),
                'service_fee': float(calculations['service_fee']),
                'total_amount_usd': float(calculations['total_amount_usd']),
                'exchange_rate': {
                    'base_rate': float(calculations['base_rate']),
                    'final_rate': float(calculations['final_rate']),
                    'spread_percentage': float(calculations['spread_percentage']),
                    'source': calculations['rate_source']
                },
                'amount_brl_estimated': float(calculations['amount_brl_estimated'])
            }
        })
        
    except ValidationError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Erro ao calcular transferência: {str(e)}")
        return Response({
            'success': False,
            'error': 'Erro interno do servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
# @jwt_required  # Temporarily commented due to JWT dependency
def create_transfer(request):
    """Cria uma nova transferência"""
    try:
        # Obter cliente autenticado
        client = request.client
        
        serializer = TransferCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        transfer_service = TransferService()
        transfer, errors = transfer_service.create_transfer(client, serializer.validated_data)
        
        if errors:
            return Response({
                'success': False,
                'errors': errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Gerar link de pagamento
        payment_link = transfer_service.generate_payment_link(transfer)
        transfer.payment_link = payment_link
        transfer.save()
        
        # Retornar dados da transferência criada
        transfer_data = TransferDetailSerializer(transfer).data
        
        return Response({
            'success': True,
            'data': transfer_data,
            'message': 'Transferência criada com sucesso'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Erro ao criar transferência: {str(e)}")
        return Response({
            'success': False,
            'error': 'Erro interno do servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
# @jwt_required  # Temporarily commented due to JWT dependency
def get_transfer(request, transfer_id):
    """Busca uma transferência específica"""
    try:
        client = request.client
        
        transfer_service = TransferService()
        transfer = transfer_service.get_transfer_by_id(transfer_id)
        
        if not transfer:
            return Response({
                'success': False,
                'error': 'Transferência não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar se a transferência pertence ao cliente
        if transfer.client != client:
            return Response({
                'success': False,
                'error': 'Acesso negado'
            }, status=status.HTTP_403_FORBIDDEN)
        
        transfer_data = TransferDetailSerializer(transfer).data
        
        return Response({
            'success': True,
            'data': transfer_data
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar transferência {transfer_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Erro interno do servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
# @jwt_required  # Temporarily commented due to JWT dependency
def list_transfers(request):
    """Lista as transferências do cliente"""
    try:
        client = request.client
        status_filter = request.GET.get('status')
        
        transfer_service = TransferService()
        transfers = transfer_service.get_client_transfers(client, status_filter)
        
        transfers_data = TransferListSerializer(transfers, many=True).data
        
        return Response({
            'success': True,
            'data': transfers_data,
            'count': len(transfers)
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar transferências do cliente {client.id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Erro interno do servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
# @jwt_required  # Temporarily commented due to JWT dependency
def update_transfer_status(request, transfer_id):
    """Atualiza o status de uma transferência"""
    try:
        client = request.client
        
        transfer_service = TransferService()
        transfer = transfer_service.get_transfer_by_id(transfer_id)
        
        if not transfer:
            return Response({
                'success': False,
                'error': 'Transferência não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar se a transferência pertence ao cliente
        if transfer.client != client:
            return Response({
                'success': False,
                'error': 'Acesso negado'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = TransferStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')
        changed_by = serializer.validated_data.get('changed_by', f'client_{client.id}')
        
        # Validar transições de status permitidas para clientes
        allowed_transitions = {
            'draft': ['cancelled'],
            'pending_payment': ['cancelled'],
            'payment_confirmed': [],  # Cliente não pode alterar após confirmação
            'processing': [],
            'completed': [],
            'cancelled': [],
            'failed': []
        }
        
        if new_status not in allowed_transitions.get(transfer.status, []):
            return Response({
                'success': False,
                'error': f'Transição de status não permitida: {transfer.status} -> {new_status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        transfer_service.update_transfer_status(transfer, new_status, changed_by, notes)
        
        transfer_data = TransferDetailSerializer(transfer).data
        
        return Response({
            'success': True,
            'data': transfer_data,
            'message': f'Status atualizado para {new_status}'
        })
        
    except ValidationError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Erro ao atualizar status da transferência {transfer_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Erro interno do servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
# @jwt_required  # Temporarily commented due to JWT dependency
def get_transfer_summary(request, transfer_id):
    """Retorna um resumo completo da transferência"""
    try:
        client = request.client
        
        transfer_service = TransferService()
        transfer = transfer_service.get_transfer_by_id(transfer_id)
        
        if not transfer:
            return Response({
                'success': False,
                'error': 'Transferência não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar se a transferência pertence ao cliente
        if transfer.client != client:
            return Response({
                'success': False,
                'error': 'Acesso negado'
            }, status=status.HTTP_403_FORBIDDEN)
        
        summary = transfer_service.get_transfer_summary(transfer)
        
        return Response({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter resumo da transferência {transfer_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Erro interno do servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
# @jwt_required  # Temporarily commented due to JWT dependency
def generate_payment_link(request, transfer_id):
    """Gera um novo link de pagamento para a transferência"""
    try:
        client = request.client
        
        transfer_service = TransferService()
        transfer = transfer_service.get_transfer_by_id(transfer_id)
        
        if not transfer:
            return Response({
                'success': False,
                'error': 'Transferência não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar se a transferência pertence ao cliente
        if transfer.client != client:
            return Response({
                'success': False,
                'error': 'Acesso negado'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Verificar se o status permite gerar link de pagamento
        if transfer.status not in ['draft', 'pending_payment']:
            return Response({
                'success': False,
                'error': f'Não é possível gerar link de pagamento para transferência com status {transfer.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Gerar novo link
        payment_link = transfer_service.generate_payment_link(transfer)
        transfer.payment_link = payment_link
        transfer.save()
        
        # Atualizar status se necessário
        if transfer.status == 'draft':
            transfer_service.update_transfer_status(
                transfer, 
                'pending_payment', 
                f'client_{client.id}', 
                'Link de pagamento gerado'
            )
        
        return Response({
            'success': True,
            'data': {
                'payment_link': payment_link,
                'transfer_id': transfer.transfer_id,
                'total_amount_usd': float(transfer.total_amount_usd)
            },
            'message': 'Link de pagamento gerado com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar link de pagamento para transferência {transfer_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Erro interno do servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
# @jwt_required  # Temporarily commented due to JWT dependency
def check_payment_status(request, transfer_id):
    """Verifica o status de pagamento de uma transferência"""
    try:
        client = request.client
        
        transfer_service = TransferService()
        transfer = transfer_service.get_transfer_by_id(transfer_id)
        
        if not transfer:
            return Response({
                'success': False,
                'error': 'Transferência não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar se a transferência pertence ao cliente
        if transfer.client != client:
            return Response({
                'success': False,
                'error': 'Acesso negado'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Se não há referência de pagamento, retornar status atual
        if not transfer.payment_reference:
            return Response({
                'success': True,
                'data': {
                    'transfer_status': transfer.status,
                    'payment_status': 'no_payment_initiated',
                    'message': 'Nenhum pagamento foi iniciado para esta transferência'
                }
            })
        
        # Verificar status no provedor de pagamento
        from ..services.payments import get_payment_status
        payment_status = get_payment_status(transfer.payment_reference)
        
        # Atualizar status da transferência se necessário
        if payment_status.get('status') == 'completed' and transfer.status == 'pending_payment':
            transfer_service.update_transfer_status(
                transfer, 
                'payment_confirmed', 
                f'client_{client.id}', 
                'Pagamento confirmado automaticamente'
            )
        elif payment_status.get('status') == 'failed' and transfer.status == 'pending_payment':
            transfer_service.update_transfer_status(
                transfer, 
                'failed', 
                f'client_{client.id}', 
                'Pagamento falhou'
            )
        
        return Response({
            'success': True,
            'data': {
                'transfer_status': transfer.status,
                'payment_status': payment_status.get('status', 'unknown'),
                'payment_amount': payment_status.get('amount'),
                'payment_currency': payment_status.get('currency'),
                'last_updated': transfer.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar status de pagamento para transferência {transfer_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Erro interno do servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Views administrativas (para uso interno/webhook)
@api_view(['PUT'])
def admin_update_transfer_status(request, transfer_id):
    """Atualiza status de transferência (uso administrativo/webhook)"""
    try:
        # Esta view seria protegida por autenticação administrativa
        # ou validação de webhook em produção
        
        transfer_service = TransferService()
        transfer = transfer_service.get_transfer_by_id(transfer_id)
        
        if not transfer:
            return Response({
                'success': False,
                'error': 'Transferência não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TransferStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')
        changed_by = serializer.validated_data.get('changed_by', 'admin')
        
        transfer_service.update_transfer_status(transfer, new_status, changed_by, notes)
        
        return Response({
            'success': True,
            'message': f'Status atualizado para {new_status}'
        })
        
    except ValidationError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Erro ao atualizar status administrativo da transferência {transfer_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Erro interno do servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)