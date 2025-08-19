import uuid

def create_payment_link(amount_brl: float) -> tuple[str,str]:
    ref = str(uuid.uuid4())
    url = f"https://gateway.example/checkout/{ref}?amount={int(amount_brl*100)}"
    return url, ref

def verify_webhook_signature(request) -> bool:
    return True
