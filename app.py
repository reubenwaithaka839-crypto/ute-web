import os
import sqlite3
import bcrypt
from flask import Flask, render_template, request, jsonify, redirect, url_for
from intasend import APIService

app = Flask(__name__)

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
    # Hardcoded admin for your professional dashboard view
    user_data = {'role': 'admin', 'name': 'Developer', 'username': 'admin_dev'}
    jobs = query_db("SELECT * FROM jobs ORDER BY id DESC LIMIT 5")
    wallet = query_db("SELECT balance FROM wallet WHERE username = ?", (user_data['username'],), one=True)
    balance = wallet['balance'] if wallet else 0.0
    return render_template('dashboard.html', user=user_data, jobs=jobs, balance=balance)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        role = request.form.get('role') # 'employee' or 'employer'
        
        # Secure password hashing
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        try:
            query_db("""INSERT INTO users (username, email, phone, password, role) 
                     VALUES (?, ?, ?, ?, ?)""", 
                     (username, email, phone, hashed, role), commit=True)
            return redirect(url_for('index'))
        except Exception as e:
            return f"Registration Error: {str(e)}"
            
    return render_template('register.html')

@app.route('/post_job', methods=['POST'])
def post_job():
    data = request.json
    query_db("INSERT INTO jobs (employer, title, description, salary) VALUES (?, ?, ?, ?)",
             (data['employer'], data['title'], data['description'], data['salary']), commit=True)
    return jsonify({"status": "success"})

@app.route('/pay', methods=['POST'])
def initiate_payment():
    try:
        response = service.collect.mpesa_stk_push(
            phone_number="254750289733", 
            email="test@example.com",
            amount=10,
            narrative="UTE Web Funding"
        )
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
