import os
import sqlite3
import bcrypt
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'supermax_vault_key_999')
DB = "ute_supermax_v4.db"

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE, email TEXT, phone TEXT, password TEXT, role TEXT, 
        bank_name TEXT, bank_account TEXT
    )""")
    cur.execute("CREATE TABLE IF NOT EXISTS wallet (username TEXT PRIMARY KEY, balance REAL DEFAULT 0.0)")
    cur.execute("CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, receiver TEXT, amount REAL, type TEXT, status TEXT DEFAULT 'completed', timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    # UPDATED JOBS TABLE
    cur.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        employer TEXT, title TEXT, description TEXT, 
        salary REAL, location TEXT, skills TEXT, status TEXT DEFAULT 'open'
    )""")
    cur.execute(query, args)
    rv = cur.fetchall()
    if commit: conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def index():
    if 'username' not in session:
        return render_template('landing.html')
    
    user = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
    wallet = query_db("SELECT balance FROM wallet WHERE username = ?", (session['username'],), one=True)
    balance = wallet['balance'] if wallet else 0.0

    if user['role'] == 'employer':
        my_jobs = query_db("SELECT * FROM jobs WHERE employer = ? ORDER BY id DESC", (user['username'],))
        return render_template('dashboard.html', user=user, balance=balance, my_jobs=my_jobs)
    else:
        # SEARCH LOGIC: If employee searches for something
        search = request.args.get('search', '')
        if search:
            available_jobs = query_db("SELECT * FROM jobs WHERE status = 'open' AND (title LIKE ? OR location LIKE ? OR skills LIKE ?)", 
                                    ('%'+search+'%', '%'+search+'%', '%'+search+'%'))
        else:
            available_jobs = query_db("SELECT * FROM jobs WHERE status = 'open' ORDER BY id DESC")
        return render_template('dashboard.html', user=user, balance=balance, available_jobs=available_jobs)

@app.route('/employer_post_job', methods=['POST'])
def employer_post_job():
    if session.get('role') != 'employer': return "Unauthorized", 403
    t = request.form.get('title')
    s = request.form.get('salary')
    l = request.form.get('location')
    sk = request.form.get('skills')
    d = request.form.get('description')
    query_db("INSERT INTO jobs (title, salary, location, skills, description, employer) VALUES (?, ?, ?, ?, ?, ?)", 
             (t, s, l, sk, d, session['username']), commit=True)
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('username'), request.form.get('password')
        user = query_db("SELECT * FROM users WHERE username = ?", (u,), one=True)
        if user and bcrypt.checkpw(p.encode('utf-8'), user['password'].encode('utf-8')):
            session['username'], session['role'] = user['username'], user['role']
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u, e, ph, p, r = request.form.get('username'), request.form.get('email'), request.form.get('phone'), request.form.get('password'), request.form.get('role')
        hashed = bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        query_db("INSERT INTO users (username, email, phone, password, role) VALUES (?, ?, ?, ?, ?)", (u, e, ph, hashed, r), commit=True)
        query_db("INSERT INTO wallet (username, balance) VALUES (?, 0.0)", (u,), commit=True)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
