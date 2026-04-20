import os
import sqlite3
import bcrypt
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from intasend import APIService
from ute import get_ute_math

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'supermax_secret_99')

# IntaSend Config
API_PUBLISHABLE_KEY = os.environ.get('INTASEND_PUBLISHABLE_KEY', '').strip()
API_TOKEN = os.environ.get('INTASEND_API_TOKEN', '').strip()
DB = "ute.db"

service = APIService(token=API_TOKEN, publishable_key=API_PUBLISHABLE_KEY, test=True)

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Supermax feature: Auto-create transactions table if missing
    cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        amount REAL,
        type TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute(query, args)
    rv = cur.fetchall()
    if commit:
        conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user_row = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
    jobs = query_db("SELECT * FROM jobs WHERE status = 'open' ORDER BY id DESC")
    wallet = query_db("SELECT balance FROM wallet WHERE username = ?", (session['username'],), one=True)
    balance = wallet['balance'] if wallet else 0.0
    
    # Get active contracts and recent transactions for dashboard preview
    contracts = query_db("SELECT * FROM contracts WHERE employee = ? OR employer = ?", (session['username'], session['username']))
    recent_tx = query_db("SELECT * FROM transactions WHERE sender = ? OR receiver = ? ORDER BY timestamp DESC LIMIT 3", 
                         (session['username'], session['username']))

    return render_template('dashboard.html', user=user_row, jobs=jobs, balance=balance, contracts=contracts, recent_tx=recent_tx)

@app.route('/history')
def history():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    txs = query_db("SELECT * FROM transactions WHERE sender = ? OR receiver = ? ORDER BY timestamp DESC", 
                   (session['username'], session['username']))
    return render_template('history.html', transactions=txs)

@app.route('/pay_contract/<int:contract_id>', methods=['POST'])
def pay_contract(contract_id):
    if session.get('role') not in ['employer', 'admin']:
        return jsonify({"error": "Unauthorized"}), 403

    contract = query_db("SELECT * FROM contracts WHERE id = ?", (contract_id,), one=True)
    if not contract:
        return jsonify({"error": "Contract not found"}), 404

    math = get_ute_math(contract['salary'], contract['total_months_paid'])
    
    try:
        # Update Balances
        query_db("UPDATE contracts SET total_months_paid = total_months_paid + 1 WHERE id = ?", (contract_id,), commit=True)
        query_db("UPDATE wallet SET balance = balance + ? WHERE username = ?", (math['net'], contract['employee']), commit=True)
        
        # RECORD TRANSACTION (The Supermax Ledger)
        query_db("INSERT INTO transactions (sender, receiver, amount, type) VALUES (?, ?, ?, ?)",
                 (session['username'], contract['employee'], math['net'], 'Salary Payment'), commit=True)
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
