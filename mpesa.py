import requests
import base64
from datetime import datetime

CONSUMER_KEY = "YOUR_KEY"
CONSUMER_SECRET = "YOUR_SECRET"
PASSKEY = "YOUR_PASSKEY"
SHORTCODE = "174379"

BASE_URL = "https://sandbox.safaricom.co.ke"

def get_token():
    url = f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    res = requests.get(url, auth=(CONSUMER_KEY, CONSUMER_SECRET))
    return res.json()["access_token"]

def stk_push(phone, amount, callback):
    token = get_token()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    password = base64.b64encode(
        (SHORTCODE + PASSKEY + timestamp).encode()
    ).decode()

    url = f"{BASE_URL}/mpesa/stkpush/v1/processrequest"

    payload = {
        "BusinessShortCode": SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": callback,
        "AccountReference": "UTE",
        "TransactionDesc": "Deposit"
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    return requests.post(url, json=payload, headers=headers).json()
