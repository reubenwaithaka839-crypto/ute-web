import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from ute import get_ute_math

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'reubbie_escrow_v13')

DB = "ute_supermax_FINAL_BOSS_V13.db"

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, role TEXT, is_verified INTEGER DEFAULT 0)")
    cur.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, salary REAL, posted_by TEXT, fee_paid INTEGER DEFAULT 0, escrow_funded INTEGER DEFAULT 0)")
    cur.execute("""CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        job_id INTEGER, 
        applicant_username TEXT,
        full_name TEXT,
        phone TEXT,
        photo_url TEXT,
        status TEXT DEFAULT 'pending'
    )""")
    cur.execute(query, args)
    if commit: conn.commit()
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/verify_employee/<username>')
def verify_employee(username):
    if session.get('username').upper() != 'REUBEN': return "Denied", 403
    query_db("UPDATE users SET is_verified = 1 WHERE username = ?", (username,), commit=True)
    return redirect(url_for('admin_room'))

@app.route('/fund_escrow/<int:job_id>', methods=['POST'])
def fund_escrow(job_id):
    # This is where the Employer deposits the salary to the Master Admin
    ref = request.form.get('ref')
    query_db("UPDATE jobs SET escrow_funded = 1 WHERE id = ?", (job_id,), commit=True)
    return "<h1>Funds Secured</h1><p>The salary is now held by UTE. You can safely hire your worker.</p><a href='/'>Back</a>"

@app.route('/')
def index():
    if 'username' not in session: return render_template('landing.html')
    user = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
    jobs = query_db("SELECT * FROM jobs WHERE fee_paid = 1 ORDER BY id DESC")
    return render_template('dashboard.html', user=user, jobs=jobs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
