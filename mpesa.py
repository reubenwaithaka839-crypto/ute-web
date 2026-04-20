import requests
from requests.auth import HTTPBasicAuth
import sqlite3
import ute
from datetime import datetime

# REPLACE WITH YOUR DARAJA CREDENTIALS
CONSUMER_KEY = 'YOUR_KEY'
CONSUMER_SECRET = 'YOUR_SECRET'
SHORTCODE = 'YOUR_PAYBILL'
PASSKEY = 'YOUR_PASSKEY'

def trigger_settlement(contract_id):
    """Processes the split: You get your cut, Employer gets cashback, Employee gets net."""
    conn = sqlite3.connect(ute.DB)
    c = conn.cursor()
    
    contract = c.execute("SELECT employer, employee, total_months_paid, salary FROM contracts WHERE id=?", (contract_id,)).fetchone()
    employer, employee, months, salary = contract
    
    math = ute.get_ute_math(salary, months)
    
    # 1. Update Ledger (Your revenue tracking)
    c.execute("INSERT INTO ledger (contract_id, gross_total, ute_share, employer_cashback, employee_net, timestamp) VALUES (?,?,?,?,?,?)",
              (contract_id, math['total'], math['ute'], math['cashback'], math['net'], datetime.now()))
    
    # 2. Update Wallets
    c.execute("UPDATE wallet SET balance = balance + ? WHERE username = ?", (math['cashback'], employer))
    c.execute("UPDATE wallet SET balance = balance + ? WHERE username = ?", (math['net'], employee))
    
    # 3. Increment the 12-month counter
    c.execute("UPDATE contracts SET total_months_paid = total_months_paid + 1 WHERE id = ?", (contract_id,))
    
    conn.commit()
    conn.close()
    return True
