import requests
from bs4 import BeautifulSoup

def dolar_comercial():
    url = "https://www.melhorcambio.com/dolar-hoje"
    r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
    r.raise_for_status()
    s = BeautifulSoup(r.text, "html.parser")
    el = s.find("input", {"id":"comercial"})
    if not el: raise RuntimeError("Cotação não encontrada")
    return float(el["value"].replace(",", "."))
