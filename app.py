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
    
    # Supermax Stats
    stats = {
        'total_users': len(query_db("SELECT id FROM users")),
        'active_jobs': len(jobs),
        'platform_earnings': 0.0 
    }

    if user_row['role'] == 'employee':
        contracts = query_db("SELECT * FROM contracts WHERE employee = ?", (session['username'],))
    else:
        contracts = query_db("SELECT * FROM contracts WHERE employer = ?", (session['username'],))

    return render_template('dashboard.html', user=user_row, jobs=jobs, balance=balance, contracts=contracts, stats=stats)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        location = request.form.get('location')
        bio = request.form.get('bio_or_company')
        query_db("UPDATE users SET location = ?, bio_or_company = ? WHERE username = ?", 
                 (location, bio, session['username']), commit=True)
        return redirect(url_for('profile'))

    user_row = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
    return render_template('profile.html', user=user_row)

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
        # Trigger M-Pesa STK Push
        service.collect.mpesa_stk_push(
            phone_number=employer_user['phone'], 
            amount=math['total'],
            narrative=f"UTE payment to {contract['employee']}"
        )
        
        query_db("UPDATE contracts SET total_months_paid = total_months_paid + 1 WHERE id = ?", (contract_id,), commit=True)
        query_db("UPDATE wallet SET balance = balance + ? WHERE username = ?", (math['net'], contract['employee']), commit=True)
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Registration, Login, Logout, Post Job routes remain the same as previous full version...

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
