import requests
import base64
from datetime import datetime

class Mpesa:

    def __init__(self, consumer_key, consumer_secret, shortcode, passkey, base_url):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.shortcode = shortcode
        self.passkey = passkey
        self.base_url = base_url

    # ================= ACCESS TOKEN =================
    def get_token(self):

        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"

        response = requests.get(url, auth=(self.consumer_key, self.consumer_secret))

        response.raise_for_status()

        return response.json()["access_token"]

    # ================= PASSWORD =================
    def generate_password(self):

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        data = f"{self.shortcode}{self.passkey}{timestamp}"

        encoded = base64.b64encode(data.encode()).decode("utf-8")

        return encoded, timestamp

    # ================= STK PUSH =================
    def stk_push(self, phone, amount, callback_url):

        token = self.get_token()

        password, timestamp = self.generate_password()

        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone,
            "PartyB": self.shortcode,
            "PhoneNumber": phone,
            "CallBackURL": callback_url,
            "AccountReference": "UTE SYSTEM",
            "TransactionDesc": "Wallet Deposit"
        }

        response = requests.post(url, json=payload, headers=headers)

        return response.json()
