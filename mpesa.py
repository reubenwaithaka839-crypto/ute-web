import requests
import base64
from datetime import datetime

# ================= CREDENTIALS =================
# Replace these with your actual keys from the Safaricom Developer Portal
CONSUMER_KEY = "YOUR_ACTUAL_CONSUMER_KEY"
CONSUMER_SECRET = "YOUR_ACTUAL_CONSUMER_SECRET"
PASSKEY = "YOUR_ACTUAL_PASSKEY"
SHORTCODE = "174379"  # Default Sandbox Shortcode

BASE_URL = "https://sandbox.safaricom.co.ke"

# ================= TOKEN GENERATION =================
def get_token():
    """Generates the OAuth2 Access Token from Safaricom"""
    url = f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    try:
        res = requests.get(url, auth=(CONSUMER_KEY, CONSUMER_SECRET))
        res.raise_for_status()
        return res.json()["access_token"]
    except Exception as e:
        print(f"Error generating token: {e}")
        return None

# ================= STK PUSH (LIPA NA MPESA) =================
def stk_push(phone, amount, callback_url):
    """Triggers the STK Push on the user's phone"""
    token = get_token()
    if not token:
        return {"error": "Failed to generate token"}

    # Safaricom requires a timestamp in YYYYMMDDHHMMSS format
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Password is a base64 encoded string of Shortcode + Passkey + Timestamp
    password_str = SHORTCODE + PASSKEY + timestamp
    password = base64.b64encode(password_str.encode()).decode()

    url = f"{BASE_URL}/mpesa/stkpush/v1/processrequest"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone, # The phone sending the money
        "PartyB": SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": "UTE_JOB_CONNECT",
        "TransactionDesc": "Wallet Deposit"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
    except Exception as e:
        return {"error": str(e)}
