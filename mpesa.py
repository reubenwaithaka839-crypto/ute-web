import os
import sqlite3
import ute
from intasend import APIService, Environment
import uuid

# Load from Render/Environment
INTASEND_TOKEN = os.environ.get("INTASEND_LIVE_TOKEN")
INTASEND_PUBLIC_KEY = os.environ.get("INTASEND_LIVE_PUBLIC_KEY")
DB = ute.DB

class RWPrestigePayments:
    def __init__(self):
        if not all([INTASEND_TOKEN, INTASEND_PUBLIC_KEY]):
            # If keys aren't set, we fall back to a dummy mode so the app doesn't crash
            self.live = False
        else:
            self.service = APIService(
                token=INTASEND_TOKEN,
                publishable_key=INTASEND_PUBLIC_KEY,
                environment=Environment.LIVE  # Change to Environment.SANDBOX for testing
            )
            self.live = True

    def initiate_stk(self, phone, amount, email, job_id):
        """Triggers the Real M-Pesa PIN prompt"""
        if not self.live:
            return {'success': False, 'error': 'System in Maintenance: API Keys Missing'}
        
        try:
            # Clean phone number for Kenya (254...)
            phone = f"254{phone.lstrip('0')}" if phone.startswith('0') else phone
            
            checkout = self.service.collect.mpesa_stk_push(
                phone_number=phone,
                email=email,
                amount=float(amount),
                narrative=f"RW Prestige Application Fee - Job #{job_id}",
                reference=f"RW_{uuid.uuid4().hex[:6]}",
                account_reference="RW_PRESTIGE"
            )
            
            self.log_txn(phone, amount, 'STK_PUSH', checkout['id'], 'pending')
            return {'success': True, 'checkout_id': checkout['id'], 'phone': phone}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def log_txn(self, phone, amount, type_txn, ref, status):
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT, amount REAL, type TEXT, ref TEXT, status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cur.execute("INSERT INTO transactions (phone, amount, type, ref, status) VALUES (?,?,?,?,?)", (phone, amount, type_txn, ref, status))
        conn.commit()
        conn.close()

payments = RWPrestigePayments()
