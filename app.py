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
    
    # Dashboard Statistics (The Supermax touch)
    stats = {
        'total_users': len(query_db("SELECT id FROM users")),
        'active_jobs': len(jobs),
        'platform_earnings': 0.0 # This would be calculated from the UTE cut
    }

    if user_row['role'] == 'employee':
        contracts = query_db("SELECT * FROM contracts WHERE employee = ?", (session['username'],))
    else:
        contracts = query_db("SELECT * FROM contracts WHERE employer = ?", (session['username'],))

    return render_template('dashboard.html', user=user_row, jobs=jobs, balance=balance, contracts=contracts, stats=stats)

@app.route('/pay_contract/<int:contract_id>', methods=['POST'])
def pay_contract(contract_id):
    if session.get('role') not in ['employer', 'admin']:
        return jsonify({"error": "Unauthorized"}), 403

    contract = query_db("SELECT * FROM contracts WHERE id = ?", (contract_id,), one=True)
    employer_user = query_db("SELECT phone FROM users WHERE username = ?", (session['username'],), one=True)

    if not contract:
        return jsonify({"error": "Contract not found"}), 404

    math = get_ute_math(contract['salary'], contract['total_months_paid'])
    
    try:
        # In Supermax mode, we trigger the real payment
        response = service.collect.mpesa_stk_push(
            phone_number=employer_user['phone'], 
            amount=math['total'],
            narrative=f"UTE payment to {contract['employee']}"
        )
        
        # Update Contract & Employee Wallet
        query_db("UPDATE contracts SET total_months_paid = total_months_paid + 1 WHERE id = ?", (contract_id,), commit=True)
        query_db("UPDATE wallet SET balance = balance + ? WHERE username = ?", (math['net'], contract['employee']), commit=True)
        
        return jsonify({"status": "success", "amount": math['total']})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Registration & Login stay the same as previous step...
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = query_db("SELECT * FROM users WHERE username = ?", (username,), one=True)
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('index'))
    return render_template('login.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
