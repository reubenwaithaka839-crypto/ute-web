import requests, base64
from datetime import datetime

# REPLACE THESE WITH YOUR SANDBOX CREDENTIALS FROM DARAJA
CONSUMER_KEY = "YOUR_KEY"
CONSUMER_SECRET = "YOUR_SECRET"
PASSKEY = "YOUR_PASSKEY"
SHORTCODE = "174379"

def get_token():
    res = requests.get("https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials", auth=(CONSUMER_KEY, CONSUMER_SECRET))
    return res.json().get("access_token")

def stk_push(phone, amount, callback):
    token = get_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode((SHORTCODE + PASSKEY + timestamp).encode()).decode()
    payload = {
        "BusinessShortCode": SHORTCODE, "Password": password, "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline", "Amount": int(amount), "PartyA": phone,
        "PartyB": SHORTCODE, "PhoneNumber": phone, "CallBackURL": callback,
        "AccountReference": "UTE_JOB_PORTAL", "TransactionDesc": "Wallet Deposit"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post("https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest", json=payload, headers=headers)
    return response.json()
