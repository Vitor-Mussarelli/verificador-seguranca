import requests
import uuid
try:
    import config
    MP_TOKEN = getattr(config, 'MERCADO_PAGO_ACCESS_TOKEN', "")
except ImportError:
    MP_TOKEN = "APP_USR-6863888755721841-041708-648f3b36a7db16d4a14fcac0f0760189-418275486"

def gerar_cobranca_pix(valor=4.90, descricao="Laudo de Auditoria Digital"):
    """
    Gera um QR Code Pix para pagamento via Mercado Pago.
    """
    if not MP_TOKEN:
        return {"erro": "Sistema de pagamento não configurado."}

    url = "https://api.mercadopago.com/v1/payments"
    headers = {
        "Authorization": f"Bearer {MP_TOKEN}",
        "X-Idempotency-Key": str(uuid.uuid4()),
        "Content-Type": "application/json"
    }
    
    payload = {
        "transaction_amount": valor,
        "description": descricao,
        "payment_method_id": "pix",
        "payer": {
            "email": "pagador@exemplo.com", # Opcional: coletar do usuário
            "first_name": "Cliente",
            "last_name": "Seguro"
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 201:
            data = response.json()
            return {
                "id": data["id"],
                "qr_code": data["point_of_interaction"]["transaction_data"]["qr_code"],
                "qr_code_base64": data["point_of_interaction"]["transaction_data"]["qr_code_base64"],
                "status": data["status"]
            }
        return {"erro": f"Erro MP: {response.status_code}"}
    except Exception as e:
        return {"erro": str(e)}

def verificar_status_pagamento(payment_id):
    if not MP_TOKEN: return False
    url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
    headers = {"Authorization": f"Bearer {MP_TOKEN}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()["status"] == "approved"
        return False
    except:
        return False
