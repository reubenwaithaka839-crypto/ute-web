import os
from intasend import APIService
import sqlite3
import ute
from datetime import datetime

# These pull from your Render "Environment Variables"
TOKEN = os.environ.get("INTASEND_TOKEN")
PUB_KEY = os.environ.get("INTASEND_PUBLISHABLE_KEY")

def initiate_stk_push(phone, amount, email, contract_id):
    if not TOKEN or not PUB_KEY:
        print("Missing API Keys in Render Settings")
        return None
    
    service = APIService(token=TOKEN, publishable_key=PUB_KEY, test_mode=True)
    try:
        return service.collect.mpesa_stk_push(
            phone_number=phone,
            email=email,
            amount=amount,
            narrative=f"UTE Payment {contract_id}"
        )
    except Exception as e:
        print(f"M-Pesa Error: {e}")
        return None

def trigger_settlement(contract_id):
    conn = sqlite3.connect(ute.DB)
    c = conn.cursor()
    contract = c.execute("SELECT employer, employee, total_months_paid, salary FROM contracts WHERE id=?", (contract_id,)).fetchone()
    
    if contract:
        employer, employee, months, salary = contract
        math = ute.get_ute_math(salary)
        
        # Split the money into virtual wallets
        c.execute("UPDATE wallet SET balance = balance + ? WHERE username = ?", (math['std_net'], employer))
        c.execute("UPDATE wallet SET balance = balance + ? WHERE username = ?", (math['placement_net'], employee))
        c.execute("UPDATE contracts SET total_months_paid = total_months_paid + 1 WHERE id = ?", (contract_id,))
        conn.commit()
    conn.close()
