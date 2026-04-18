import requests
import base64
from datetime import datetime

# -----------------------------
# CONFIG (REPLACE WITH YOUR KEYS)
# -----------------------------
CONSUMER_KEY = "YOUR_CONSUMER_KEY"
CONSUMER_SECRET = "YOUR_CONSUMER_SECRET"
BUSINESS_SHORTCODE = "174379"
PASSKEY = "YOUR_PASSKEY"

BASE_URL = "https://sandbox.safaricom.co.ke"  # change to live later

# -----------------------------
# ACCESS TOKEN
# -----------------------------
def get_token():
    url = f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(CONSUMER_KEY, CONSUMER_SECRET))
    return response.json()["access_token"]

# -----------------------------
# STK PUSH
# -----------------------------
def stk_push(phone, amount, callback_url):
    token = get_token()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(
        (BUSINESS_SHORTCODE + PASSKEY + timestamp).encode()
    ).decode()

    url = f"{BASE_URL}/mpesa/stkpush/v1/processrequest"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": BUSINESS_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": BUSINESS_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": "UTE FINTECH",
        "TransactionDesc": "Wallet Deposit"
    }

    response = requests.post(url, json=payload, headers=headers)

    print("📡 STK PUSH SENT")
    return response.json()
