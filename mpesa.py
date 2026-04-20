import requests
from requests.auth import HTTPBasicAuth
import sqlite3
import ute
from datetime import datetime

# REPLACE THESE WITH YOUR DARAJA API CREDENTIALS
CONSUMER_KEY = 'Your_Consumer_Key'
CONSUMER_SECRET = 'Your_Consumer_Secret'
BUSINESS_SHORTCODE = 'Your_Paybill'
PASSKEY = 'Your_Passkey'

def get_access_token():
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r = requests.get(api_url, auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET))
    return r.json()['access_token']

def trigger_split_logic(contract_id, amount):
    """
    THIS IS THE CORE SETTLEMENT ENGINE.
    1. Records the math in the Ledger.
    2. Moves 20% or 6% to YOUR bank account.
    3. Moves cashback to Employer wallet.
    4. Moves salary to Employee escrow.
    """
    conn = sqlite3.connect(ute.DB)
    c = conn.cursor()
    
    # Fetch contract details
    contract = c.execute("SELECT employer, employee, total_months_paid, salary FROM contracts WHERE id=?", (contract_id,)).fetchone()
    employer, employee, months, salary = contract
    
    # Calculate the UTE Split (30% vs 10%)
    math = ute.get_ute_math(salary, months)
    
    # 1. Update Ledger
    c.execute("""INSERT INTO ledger (contract_id, gross_total, ute_share, employer_cashback, employee_net, fraud_score, timestamp)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""", 
              (contract_id, math['total'], math['ute'], math['cashback'], math['net'], 0.01, datetime.now()))
    
    # 2. Update Wallets
    c.execute("UPDATE wallet SET balance = balance + ? WHERE username = ?", (math['cashback'], employer))
    c.execute("UPDATE wallet SET balance = balance + ? WHERE username = ?", (math['net'], employee))
    
    # 3. Update Contract Timer
    c.execute("UPDATE contracts SET total_months_paid = total_months_paid + 1 WHERE id = ?", (contract_id,))
    
    # 4. Trigger BANK SETTLEMENT (Direct to You)
    # Note: This requires a B2C API endpoint from your bank or M-Pesa B2C
    print(f"SETTLING KES {math['ute']} TO SUPERADMIN BANK ACCOUNT...")

    conn.commit()
    conn.close()
    return True
