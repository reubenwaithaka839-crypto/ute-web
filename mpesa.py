import os
import sqlite3
import ute
from intasend import APIService, Environment
import uuid

# Keys from IntaSend Sandbox (No KRA needed for Sandbox)
INTASEND_TOKEN = os.environ.get("INTASEND_TOKEN")
INTASEND_PUB_KEY = os.environ.get("INTASEND_PUB_KEY")
DB = ute.DB

class RWPrestigePayments:
    def __init__(self):
        # We use Environment.SANDBOX for students/testing
        self.service = APIService(
            token=INTASEND_TOKEN,
            publishable_key=INTASEND_PUB_KEY,
            environment=Environment.SANDBOX 
        )

    def initiate_mpesa_stk(self, phone, amount, email, job_id):
        try:
            phone = f"254{phone.lstrip('0')}" if phone.startswith('0') else phone
            checkout = self.service.collect.mpesa_stk_push(
                phone_number=phone,
                email=email,
                amount=float(amount),
                narrative=f"RW Application Fee - Job {job_id}",
                reference=f"RW_{uuid.uuid4().hex[:6]}",
                account_reference="RW_PRESTIGE"
            )
            return {'success': True, 'checkout_id': checkout['id'], 'phone': phone}
        except Exception as e:
            return {'success': False, 'error': str(e)}

payments = RWPrestigePayments()
