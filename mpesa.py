import requests
import base64
from datetime import datetime

class Mpesa:

    def __init__(self):
        self.consumer_key = "YOUR_CONSUMER_KEY"
        self.consumer_secret = "YOUR_CONSUMER_SECRET"
        self.shortcode = "174379"  # sandbox or paybill
        self.passkey = "YOUR_PASSKEY"
        self.base_url = "https://sandbox.safaricom.co.ke"

    # ================= ACCESS TOKEN =================
    def get_token(self):
        url = self.base_url + "/oauth/v1/generate?grant_type=client_credentials"

        response = requests.get(
            url,
            auth=(self.consumer_key, self.consumer_secret)
        )

        return response.json()["access_token"]

    # ================= STK PUSH =================
    def stk_push(self, phone, amount, callback_url):

        token = self.get_token()

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        password = base64.b64encode(
            (self.shortcode + self.passkey + timestamp).encode()
        ).decode()

        url = self.base_url + "/mpesa/stkpush/v1/processrequest"

        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json"
        }

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": self.shortcode,
            "PhoneNumber": phone,
            "CallBackURL": callback_url,
            "AccountReference": "UTE SYSTEM",
            "TransactionDesc": "Payment"
        }

        response = requests.post(url, json=payload, headers=headers)

        return response.json()
