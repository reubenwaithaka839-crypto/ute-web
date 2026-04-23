import os
import sqlite3
import requests
from cryptography.fernet import Fernet
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
import base64

DB = "rw_prestige_final.db"
KEY = os.environ.get('LOGIC_KEY', Fernet.generate_key().decode())
cipher = Fernet(KEY.encode())

def calculate_prestige_split(gross_salary, is_first_month=True):
    total_gross = float(gross_salary)
    transaction_fee = total_gross * 0.03
    
    if is_first_month:
        total_deduction = total_gross * 0.30
        employee_earns = total_gross * 0.70
        employer_rebate = total_gross * 0.10
    else:
        total_deduction = total_gross * 0.10
        employee_earns = total_gross * 0.90
        employer_rebate = total_gross * 0.02

    return {
        "gross": total_gross,
        "employee_net": employee_earns,
        "employer_rebate": employer_rebate,
        "treasury_total": (total_deduction - employer_rebate) + transaction_fee
    }

class JengaHQ:
    def __init__(self):
        self.base_url = "https://api.jengahq.io" # Live URL
        self.merchant_id = os.environ.get('JENGA_MERCHANT_ID')
        self.api_key = os.environ.get('JENGA_API_KEY')

    def get_token(self):
        url = f"{self.base_url}/authentication/v1/login"
        payload = {"merchantCode": self.merchant_id, "consumerSecret": self.api_key}
        try:
            r = requests.post(url, json=payload)
            return r.json().get('accessToken')
        except: return None

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE, 
        passcode TEXT, 
        role TEXT, 
        balance REAL DEFAULT 0,
        equity_acc TEXT,
        kra_pin TEXT)""")
    cur.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, salary REAL, poster TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS applications (id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER, applicant TEXT, status TEXT DEFAULT 'pending')")
    cur.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, room_id TEXT, sender TEXT, text TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    conn.close()
