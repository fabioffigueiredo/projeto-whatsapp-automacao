import requests
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class FXService:
    """Serviço para obter cotações de câmbio"""
    
    def get_usd_to_brl_rate(self):
        """Obtém a cotação USD para BRL"""
        return dolar_comercial()

def dolar_comercial():
    """
    Obtém cotação do dólar comercial com fallback para múltiplas APIs.
    Retorna: float com a cotação atual
    """
    # API primária: AwesomeAPI (mais estável)
    try:
        return _get_rate_awesomeapi()
    except Exception as e:
        logger.warning(f"AwesomeAPI falhou: {e}")
    
    # Fallback 1: Fixer.io (backup)
    try:
        return _get_rate_fixer()
    except Exception as e:
        logger.warning(f"Fixer.io falhou: {e}")
    
    # Fallback 2: Web scraping (último recurso)
    try:
        return _get_rate_scraping()
    except Exception as e:
        logger.error(f"Todos os métodos falharam. Último erro: {e}")
        # Retorna cotação padrão em caso de falha total
        return 5.50

def _get_rate_awesomeapi():
    """API primária - AwesomeAPI"""
    url = "https://economia.awesomeapi.com.br/last/USD-BRL"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    return float(data["USDBRL"]["bid"])

def _get_rate_fixer():
    """Fallback 1 - Fixer.io (requer API key em produção)"""
    # Para desenvolvimento, usar versão gratuita limitada
    url = "http://data.fixer.io/api/latest?access_key=YOUR_API_KEY&symbols=BRL&base=USD"
    # Em desenvolvimento, simular resposta ou usar API gratuita alternativa
    raise NotImplementedError("Configurar API key do Fixer.io")

def _get_rate_scraping():
    """Fallback 2 - Web scraping (último recurso)"""
    from bs4 import BeautifulSoup
    
    url = "https://www.melhorcambio.com/dolar-hoje"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    element = soup.find("input", {"id": "comercial"})
    if not element:
        raise RuntimeError("Cotação não encontrada no scraping")
    
    return float(element["value"].replace(",", "."))