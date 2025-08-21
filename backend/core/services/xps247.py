import logging
import requests
from django.conf import settings
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def find_client_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    """
    Busca cliente no sistema XPS247 pelo telefone
    
    Args:
        phone (str): Número de telefone do cliente
    
    Returns:
        dict: Dados do cliente se encontrado, None caso contrário
    """
    try:
        # Configurações da API XPS247
        xps247_api_url = getattr(settings, 'XPS247_API_URL', None)
        xps247_api_key = getattr(settings, 'XPS247_API_KEY', None)
        
        if not xps247_api_url or not xps247_api_key:
            logger.warning("XPS247 API not configured, using mock data")
            return _get_mock_client(phone)
        
        # Fazer requisição para a API XPS247
        headers = {
            'Authorization': f'Bearer {xps247_api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{xps247_api_url}/clients/search",
            params={'phone': phone},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('clients'):
                client = data['clients'][0]  # Pegar o primeiro resultado
                return {
                    'name': client.get('name'),
                    'cpf': client.get('cpf'),
                    'phone': client.get('phone'),
                    'verified': client.get('verified', False),
                    'xps247_id': client.get('id')
                }
        elif response.status_code == 404:
            logger.info(f"Client not found in XPS247 for phone: {phone}")
            return None
        else:
            logger.error(f"XPS247 API error: {response.status_code} - {response.text}")
            return _get_mock_client(phone)
            
    except requests.RequestException as e:
        logger.error(f"Error connecting to XPS247 API: {e}")
        return _get_mock_client(phone)
    except Exception as e:
        logger.error(f"Unexpected error in find_client_by_phone: {e}")
        return _get_mock_client(phone)
    
    return None


def _get_mock_client(phone: str) -> Dict[str, Any]:
    """
    Retorna dados mock de cliente para desenvolvimento/fallback
    
    Args:
        phone (str): Número de telefone
    
    Returns:
        dict: Dados mock do cliente
    """
    return {
        "name": "Cliente Exemplo",
        "cpf": "123.456.789-00",
        "phone": phone,
        "verified": False,
        "xps247_id": "mock_id"
    }


def create_client(client_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Cria um novo cliente no sistema XPS247
    
    Args:
        client_data (dict): Dados do cliente
    
    Returns:
        dict: Dados do cliente criado
    """
    try:
        xps247_api_url = getattr(settings, 'XPS247_API_URL', None)
        xps247_api_key = getattr(settings, 'XPS247_API_KEY', None)
        
        if not xps247_api_url or not xps247_api_key:
            logger.warning("XPS247 API not configured, using mock creation")
            return {**client_data, 'xps247_id': 'mock_created_id'}
        
        headers = {
            'Authorization': f'Bearer {xps247_api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{xps247_api_url}/clients",
            json=client_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            logger.error(f"Error creating client in XPS247: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating client in XPS247: {e}")
        return None


def find_beneficiary_by_cpf(cpf: str) -> Optional[Dict[str, Any]]:
    """
    Busca beneficiário no sistema XPS247 pelo CPF
    
    Args:
        cpf (str): CPF do beneficiário
    
    Returns:
        dict: Dados do beneficiário se encontrado, None caso contrário
    """
    try:
        xps247_api_url = getattr(settings, 'XPS247_API_URL', None)
        xps247_api_key = getattr(settings, 'XPS247_API_KEY', None)
        
        if not xps247_api_url or not xps247_api_key:
            logger.warning("XPS247 API not configured, simulating beneficiary not found")
            # Em desenvolvimento, simula que o beneficiário não foi encontrado
            # para testar o fluxo de cadastro
            return None
        
        headers = {
            'Authorization': f'Bearer {xps247_api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{xps247_api_url}/beneficiaries/search",
            params={'cpf': cpf},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('beneficiaries'):
                beneficiary = data['beneficiaries'][0]  # Pegar o primeiro resultado
                return {
                    'name': beneficiary.get('name'),
                    'cpf': beneficiary.get('cpf'),
                    'pix_key': beneficiary.get('pix_key'),
                    'address': beneficiary.get('address'),
                    'xps247_id': beneficiary.get('id')
                }
        elif response.status_code == 404:
            logger.info(f"Beneficiary not found in XPS247 for CPF: {cpf}")
            return None
        else:
            logger.error(f"XPS247 API error: {response.status_code} - {response.text}")
            return None
            
    except requests.RequestException as e:
        logger.error(f"Error connecting to XPS247 API: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in find_beneficiary_by_cpf: {e}")
        return None
    
    return None


def verify_client_cpf(xps247_id: str, cpf: str) -> bool:
    """
    Verifica se o CPF do cliente está correto no sistema XPS247
    
    Args:
        xps247_id (str): ID do cliente no XPS247
        cpf (str): CPF para verificação
    
    Returns:
        bool: True se o CPF estiver correto
    """
    try:
        xps247_api_url = getattr(settings, 'XPS247_API_URL', None)
        xps247_api_key = getattr(settings, 'XPS247_API_KEY', None)
        
        if not xps247_api_url or not xps247_api_key:
            logger.warning("XPS247 API not configured, using mock verification")
            return True  # Em desenvolvimento, sempre retorna True
        
        headers = {
            'Authorization': f'Bearer {xps247_api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{xps247_api_url}/clients/{xps247_id}/verify-cpf",
            json={'cpf': cpf},
            headers=headers,
            timeout=10
        )
        
        return response.status_code == 200 and response.json().get('verified', False)
        
    except Exception as e:
        logger.error(f"Error verifying CPF in XPS247: {e}")
        return False
