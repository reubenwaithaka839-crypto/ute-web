import requests
import base64
from datetime import datetime

class Mpesa:

    def __init__(self, key, secret, shortcode, passkey, base_url):
        self.key = key
        self.secret = secret
        self.shortcode = shortcode
        self.passkey = passkey
        self.base_url = base_url

    def get_token(self):
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        res = requests.get(url, auth=(self.key, self.secret))
        return res.json()["access_token"]

    def generate_password(self):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        data = f"{self.shortcode}{self.passkey}{timestamp}"
        return base64.b64encode(data.encode()).decode(), timestamp

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
            "AccountReference": "UTE",
            "TransactionDesc": "Payment"
        }

        return requests.post(url, json=payload, headers=headers).json()
