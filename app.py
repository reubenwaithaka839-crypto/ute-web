import os
import sqlite3
import ute
import mpesa  # This imports our RWPrestigePayments logic
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

app = Flask(__name__)
app.secret_key = 'RW_ULTIMATE_PRESTIGE_2026_SECURE_V3_XYZ'
DB = ute.DB

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute(query, args)
        if commit: conn.commit()
        rv = cur.fetchall()
        return (rv[0] if rv else None) if one else rv
    except Exception as e:
        return None if one else []
    finally:
        conn.close()

@app.route('/')
def portal():
    return render_template('portal.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username', '').strip()
        session['username'] = u
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session: return redirect(url_for('portal'))
    user = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
    if user and (user['role'] == 'admin' or user['username'].upper() == 'REUBEN'): 
        return redirect(url_for('admin_panel'))
    jobs = query_db("SELECT * FROM jobs")
    return render_template('dashboard.html', user=user, jobs=jobs)

# --- NEW PAYMENT SYSTEM ---

@app.route('/pay/<int:job_id>')
def pay_page(job_id):
    if 'username' not in session: return redirect(url_for('portal'))
    job = query_db("SELECT * FROM jobs WHERE id = ?", (job_id,), one=True)
    user = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
    
    # 5% Business Fee logic
    fee = float(job['salary']) * 0.05
    return render_template('payment.html', amount=fee, job=job, user=user)

@app.route('/process_payment', methods=['POST'])
def process_payment():
    if 'username' not in session: return jsonify({'success': False, 'error': 'Login required'})
    
    job_id = request.form.get('job_id')
    phone = request.form.get('phone')
    email = request.form.get('email')
    
    job = query_db("SELECT salary FROM jobs WHERE id = ?", (job_id,), one=True)
    fee = float(job['salary']) * 0.05
    
    # Trigger the Bank Integration
    result = mpesa.payments.initiate_stk(phone, fee, email, job_id)
    return jsonify(result)

@app.route('/admin_panel')
def admin_panel():
    if session.get('username','').upper() != 'REUBEN': return "UNAUTHORIZED", 403
    stats = {
        'total_users': query_db("SELECT COUNT(*) as count FROM users", one=True)['count'],
        'live_jobs': query_db("SELECT COUNT(*) as count FROM jobs", one=True)['count'],
        'total_applications': query_db("SELECT COUNT(*) as count FROM applications", one=True)['count'],
        'total_employers': query_db("SELECT COUNT(*) as count FROM users WHERE role='employer' OR bank_name IS NOT NULL", one=True)['count'],
    }
    txns = query_db("SELECT * FROM transactions ORDER BY created_at DESC LIMIT 10")
    return render_template('admin_pannel.html', stats=stats, transactions=txns)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('portal'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
