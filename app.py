import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'reubbie_v16_logo_empire')

DB = "ute_final_empire.db"

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # PRESTIGE DATABASE SCHEMA
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, role TEXT, is_verified INTEGER DEFAULT 0)")
    cur.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, location TEXT, salary REAL, posted_by TEXT, fee_paid INTEGER DEFAULT 0)")
    cur.execute("""CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER, applicant_username TEXT,
        full_name TEXT, id_number TEXT, phone TEXT, email TEXT, gender TEXT, 
        age INTEGER, location TEXT, skills TEXT, photo_url TEXT, status TEXT DEFAULT 'pending'
    )""")
    cur.execute(query, args)
    if commit: conn.commit()
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def index():
    if 'username' not in session: return redirect(url_for('login'))
    user = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
    jobs = query_db("SELECT * FROM jobs WHERE fee_paid = 1 ORDER BY id DESC")
    my_jobs = query_db("SELECT * FROM jobs WHERE posted_by = ?", (session['username'],))
    my_apps = query_db("SELECT job_id FROM applications WHERE applicant_username = ?", (session['username'],))
    applied_ids = [app['job_id'] for app in my_apps]
    return render_template('dashboard.html', user=user, jobs=jobs, my_jobs=my_jobs, applied_ids=applied_ids)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username').strip()
        # REUBEN GHOST PROTOCOL
        role = 'admin' if u.upper() == 'REUBEN' else request.form.get('role')
        user = query_db("SELECT * FROM users WHERE username = ?", (u,), one=True)
        if not user:
            query_db("INSERT INTO users (username, role) VALUES (?, ?)", (u, role), commit=True)
            user = query_db("SELECT * FROM users WHERE username = ?", (u,), one=True)
        session['username'], session['role'] = user['username'], user['role']
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/post_job', methods=['POST'])
def post_job():
    if session.get('role') not in ['employer', 'admin']: return "Unauthorized", 403
    t, l, s = request.form.get('title'), request.form.get('location'), request.form.get('salary')
    query_db("INSERT INTO jobs (title, location, salary, posted_by, fee_paid) VALUES (?, ?, ?, ?, 0)", (t, l, s, session['username']), commit=True)
    job = query_db("SELECT id FROM jobs ORDER BY id DESC LIMIT 1", one=True)
    return redirect(url_for('payment_gate', job_id=job['id']))

@app.route('/payment_gate/<int:job_id>')
def payment_gate(job_id):
    return render_template('payment_gate.html', job_id=job_id)

@app.route('/verify_payment/<int:job_id>', methods=['POST'])
def verify_payment(job_id):
    query_db("UPDATE jobs SET fee_paid = 1 WHERE id = ?", (job_id,), commit=True)
    return redirect(url_for('index'))

@app.route('/apply_form/<int:job_id>')
def apply_form(job_id):
    job = query_db("SELECT * FROM jobs WHERE id = ?", (job_id,), one=True)
    return render_template('apply_form.html', job=job)

@app.route('/submit_application', methods=['POST'])
def submit_application():
    data = (request.form.get('job_id'), session['username'], request.form.get('full_name'), request.form.get('id_number'), request.form.get('phone'), request.form.get('email'), request.form.get('gender'), request.form.get('age'), request.form.get('location'), request.form.get('skills'), request.form.get('photo_url'))
    query_db("INSERT INTO applications (job_id, applicant_username, full_name, id_number, phone, email, gender, age, location, skills, photo_url) VALUES (?,?,?,?,?,?,?,?,?,?,?)", data, commit=True)
    return redirect(url_for('index'))

@app.route('/view_applicants/<int:job_id>')
def view_applicants(job_id):
    job = query_db("SELECT * FROM jobs WHERE id = ?", (job_id,), one=True)
    if job['posted_by'] != session['username'] and session.get('role') != 'admin': return "Unauthorized", 403
    applicants = query_db("SELECT * FROM applications WHERE job_id = ?", (job_id,))
    return render_template('view_applicants.html', job=job, applicants=applicants)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
