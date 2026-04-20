import os
import sqlite3
import bcrypt
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from intasend import APIService

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'ute_web_secret_12345')

# Config
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
    
    # Get current user's wallet
    wallet = query_db("SELECT balance FROM wallet WHERE username = ?", (session['username'],), one=True)
    balance = wallet['balance'] if wallet else 0.0
    
    # Get active contracts for this user
    if user_row['role'] == 'employee':
        contracts = query_db("SELECT * FROM contracts WHERE employee = ?", (session['username'],))
    else:
        contracts = query_db("SELECT * FROM contracts WHERE employer = ?", (session['username'],))

    return render_template('dashboard.html', user=user_row, jobs=jobs, balance=balance, contracts=contracts)

@app.route('/apply/<int:job_id>', methods=['POST'])
def apply_job(job_id):
    if 'username' not in session or session.get('role') != 'employee':
        return jsonify({"error": "Only employees can apply"}), 403

    # Get job details
    job = query_db("SELECT * FROM jobs WHERE id = ?", (job_id,), one=True)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    # Create contract and close the job listing
    query_db("INSERT INTO contracts (employer, employee, salary) VALUES (?, ?, ?)",
             (job['employer'], session['username'], job['salary']), commit=True)
    
    query_db("UPDATE jobs SET status = 'closed' WHERE id = ?", (job_id,), commit=True)
    
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        phone = request.form.get('phone').strip()
        password = request.form.get('password')
        role = request.form.get('role')
        
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        try:
            query_db("INSERT INTO users (username, email, phone, password, role) VALUES (?, ?, ?, ?, ?)", 
                     (username, email, phone, hashed, role), commit=True)
            # Create a wallet for the new user
            query_db("INSERT INTO wallet (username, balance) VALUES (?, 0)", (username,), commit=True)
            return redirect(url_for('login'))
        except:
            return "Registration Error: User might already exist."
    return render_template('register.html')

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
        return "Invalid Login Credentials"
    return render_template('login.html')

@app.route('/post_job', methods=['POST'])
def post_job():
    if session.get('role') not in ['employer', 'admin']:
        return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    query_db("INSERT INTO jobs (employer, title, description, salary) VALUES (?, ?, ?, ?)",
             (session['username'], data['title'], data['description'], data['salary']), commit=True)
    return jsonify({"status": "success"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
