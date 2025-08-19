def find_client_by_phone(phone: str):
    if phone.endswith("123"):
        return {"external_id": "XPS-42", "name": "Cliente Demo", "phone": phone, "email": "c@demo.com"}
    return None
