from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import WebhookIn, PaymentWebhookIn
from .models import Conversation, MessageLog, Client, Operation
from .services.fx import dolar_comercial
from .services.payments import create_payment_link, verify_webhook_signature
from .services.xps247 import find_client_by_phone
from decimal import Decimal

@api_view(["POST"])
def whatsapp_webhook(request):
    ser = WebhookIn(data=request.data)
    ser.is_valid(raise_exception=True)
    phone = ser.validated_data["phone"]
    text = ser.validated_data["message"].strip().lower()

    conv, _ = Conversation.objects.get_or_create(external_user_id=phone)
    MessageLog.objects.create(conversation=conv, direction="in", payload=request.data)

    if conv.state_node == "START":
        quote = dolar_comercial()
        reply = f"Olá! Dólar comercial hoje: R$ {quote:.2f}\nDeseja iniciar uma transferência?\n1 - Sim\n2 - Não"
        conv.state_node = "ASK_START"; conv.save()
        MessageLog.objects.create(conversation=conv, direction="out", payload={"reply": reply})
        return Response({"reply": reply})

    if conv.state_node == "ASK_START":
        if text == "1":
            client_info = find_client_by_phone(phone)
            if client_info:
                client, _ = Client.objects.get_or_create(
                    phone=phone,
                    defaults={"name": client_info["name"], "email": client_info.get("email"), "external_id": client_info["external_id"]}
                )
                reply = f"Olá {client.name}! Informe o valor em USD:"
                conv.state_node = "ASK_AMOUNT_USD"
            else:
                reply = "Você ainda não está cadastrado. Envie seu CPF para iniciarmos o cadastro:"
                conv.state_node = "ASK_CPF"
        else:
            reply = "Ok! Se precisar de ajuda, envie 'oi'."
            conv.state_node = "END"
        conv.save()
        MessageLog.objects.create(conversation=conv, direction="out", payload={"reply": reply})
        return Response({"reply": reply})

    if conv.state_node == "ASK_CPF":
        reply = "CPF recebido. Qual valor em USD você deseja enviar?"
        conv.state_node = "ASK_AMOUNT_USD"; conv.save()
        MessageLog.objects.create(conversation=conv, direction="out", payload={"reply": reply})
        return Response({"reply": reply})

    if conv.state_node == "ASK_AMOUNT_USD":
        try:
            amount_usd = Decimal(text.replace(",", "."))
        except:
            return Response({"reply": "Valor inválido. Envie algo como 150.00"})
        rate = Decimal(str(dolar_comercial()))
        fees = Decimal("5.00")
        amount_brl = (amount_usd * rate) - fees
        reply = (
            f"Você envia ${amount_usd} a R$ {rate:.2f}. Taxas R$ {fees:.2f}. "
            f"Estimativa a receber: R$ {amount_brl:.2f}.\n1 - Confirmar\n2 - Alterar"
        )
        conv.state_node = f"CONFIRM|{amount_usd}|{rate}|{fees}|{amount_brl}"
        conv.save()
        MessageLog.objects.create(conversation=conv, direction="out", payload={"reply": reply})
        return Response({"reply": reply})

    if conv.state_node.startswith("CONFIRM"):
        parts = conv.state_node.split("|")
        amount_usd = Decimal(parts[1]); rate = Decimal(parts[2]); fees = Decimal(parts[3]); amount_brl = Decimal(parts[4])
        if text == "1":
            client = Client.objects.filter(phone=phone).first()
            if not client:
                return Response({"reply":"Cadastre-se primeiro enviando CPF."})
            op = Operation.objects.create(
                client=client, amount_usd=amount_usd, rate_used=rate,
                fees=fees, amount_brl_estimated=amount_brl, status="awaiting_payment"
            )
            url, ref = create_payment_link(float(amount_brl))
            op.payment_link = url; op.payment_provider_ref = ref; op.save()
            reply = f"Link de pagamento (20 min): {url}\nApós o pagamento, confirmamos aqui."
            conv.state_node = "WAIT_PAYMENT"
        else:
            reply = "Sem problemas! Envie o novo valor em USD."
            conv.state_node = "ASK_AMOUNT_USD"
        conv.save()
        MessageLog.objects.create(conversation=conv, direction="out", payload={"reply": reply})
        return Response({"reply": reply})

    if conv.state_node == "WAIT_PAYMENT":
        return Response({"reply": "Aguardando confirmação do pagamento..."})

    return Response({"reply": "Digite 'oi' para começar."})

@api_view(["POST"])
def payment_webhook(request):
    if not verify_webhook_signature(request):
        return Response({"ok": False, "error": "invalid signature"}, status=403)

    ser = PaymentWebhookIn(data=request.data)
    ser.is_valid(raise_exception=True)
    ref = ser.validated_data["ref"]
    status_in = ser.validated_data["status"]

    op = Operation.objects.filter(payment_provider_ref=ref).first()
    if not op:
        return Response({"ok": False, "error": "operation not found"}, status=404)

    if status_in == "paid":
        op.status = "paid"
    elif status_in == "failed":
        op.status = "failed"
    op.save()
    return Response({"ok": True})
