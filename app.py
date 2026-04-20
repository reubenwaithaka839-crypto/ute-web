import os
import sqlite3
import bcrypt
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from intasend import APIService
from ute import get_ute_math # Importing your specific math formula

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_secret_for_dev')

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
    
    # Get active contracts
    if user_row['role'] == 'employee':
        contracts = query_db("SELECT * FROM contracts WHERE employee = ?", (session['username'],))
    else:
        contracts = query_db("SELECT * FROM contracts WHERE employer = ?", (session['username'],))

    return render_template('dashboard.html', user=user_row, jobs=jobs, balance=balance, contracts=contracts)

@app.route('/pay_contract/<int:contract_id>', methods=['POST'])
def pay_contract(contract_id):
    if session.get('role') not in ['employer', 'admin']:
        return jsonify({"error": "Only employers can initiate payments"}), 403

    contract = query_db("SELECT * FROM contracts WHERE id = ?", (contract_id,), one=True)
    employer_user = query_db("SELECT phone FROM users WHERE username = ?", (session['username'],), one=True)

    if not contract or not employer_user:
        return jsonify({"error": "Contract or User not found"}), 404

    # Calculate the UTE Split using your formula
    math = get_ute_math(contract['salary'], contract['total_months_paid'])
    
    try:
        # Trigger M-Pesa STK Push for the 'Total' (Salary + 3% Fee)
        response = service.collect.mpesa_stk_push(
            phone_number=employer_user['phone'], 
            email="payments@ute-web.com",
            amount=math['total'],
            narrative=f"Salary for {contract['employee']}"
        )
        
        # LOGIC: In a real app, we'd wait for a webhook. 
        # For now, let's update the contract months as if it passed.
        query_db("UPDATE contracts SET total_months_paid = total_months_paid + 1 WHERE id = ?", (contract_id,), commit=True)
        
        # Add the Net salary to the employee's wallet
        query_db("UPDATE wallet SET balance = balance + ? WHERE username = ?", (math['net'], contract['employee']), commit=True)
        
        return jsonify({"status": "STK Push Sent", "details": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Include your existing /login, /register, and /post_job routes here...

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
