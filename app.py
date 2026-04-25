from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
from datetime import datetime
from flask_daraja import Daraja
from ute import calculate_prestige_split 

app = Flask(__name__)
app.secret_key = "RW_SUPERMAX_SECRET_2026"
DB_PATH = "rw_prestige_final.db"

# ==============================
# DARAJA API CONFIGURATION (M-PESA)
# ==============================
# GET THESE FROM https://developer.safaricom.co.ke
# 1. CONSUMER_KEY
# 2. CONSUMER_SECRET
# 3. PASS_KEY (Lipa Na M-Pesa Online Shortcode Password)
# 4. CallBackURL: This must be a public URL (Use Ngrok for testing) e.g., https://your-app.ngrok.io/mpesa/callback
# ==============================

CONSUMER_KEY = "YOUR_SAFARICOM_CONSUMER_KEY_HERE"
CONSUMER_SECRET = "YOUR_SAFARICOM_CONSUMER_SECRET_HERE"
PASS_KEY = "YOUR_SAFARICOM_PASSKEY_HERE"

# Initialize Daraja
# Environment: "sandbox" for testing, "production" for real money
try:
    daraja = Daraja(
        consumer_key=CONSUMER_KEY, 
        consumer_secret=CONSUMER_SECRET, 
        app_key=PASS_KEY, 
        environment="sandbox"
    )
except Exception as e:
    print(f"DARAJA WARNING: API keys not set yet. {e}")
    daraja = None

# ==============================
# DATABASE INITIALIZATION
# ==============================
def force_init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT, contacts TEXT, 
        passcode TEXT, role TEXT, is_admin INTEGER DEFAULT 0, equity_acc TEXT,
        balance REAL DEFAULT 0.0, location TEXT, bio_or_company TEXT, skills TEXT,
        expected_salary REAL, photo_url TEXT,
        business_reg_no TEXT, is_verified_business INTEGER DEFAULT 0, kra_pin TEXT)""")
        
    cur.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY, title TEXT, description TEXT, salary REAL, 
        poster TEXT, status TEXT DEFAULT 'active',
        location TEXT, skills_required TEXT, deadline TEXT, job_contacts TEXT)""")
        
    cur.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY, room_id TEXT, sender TEXT, text TEXT, 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
        
    cur.execute("""CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY, job_id INTEGER, applicant_username TEXT,
        full_name TEXT, age INTEGER, gender TEXT, phone TEXT, email TEXT,
        photo_url TEXT, skills TEXT, documents_url TEXT, status TEXT DEFAULT 'Pending',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
        
    cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY, sender TEXT, receiver TEXT, amount REAL,
        type TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    
    # --- HARDCODED GOD ADMIN (REUBEN) ---
    cur.execute("INSERT OR IGNORE INTO users (username, passcode, role, is_admin, is_verified_business) VALUES (?, ?, ?, 1, 1)",
               ('REUBEN', 'I LOVE MY MOTHER 20071975OCTDEC', 'admin'))
    
    conn.commit()
    conn.close()

force_init_db()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    def wrap(*args, **kwargs):
        if 'username' not in session: return redirect(url_for('portal'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

def super_admin_required(f):
    """Only 'REUBEN' can access this."""
    def wrap(*args, **kwargs):
        if 'username' not in session: return redirect(url_for('portal'))
        if session['username'] != 'REUBEN': return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

# ==============================
# WEB ROUTES
# ==============================

@app.route('/')
def portal():
    return render_template('portal.html')

@app.route('/terms', methods=['GET', 'POST'])
def terms():
    if request.method == 'POST':
        session['terms_accepted'] = True
        return redirect(url_for('register'))
    return render_template('terms.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if not session.get('terms_accepted'): return redirect(url_for('terms'))
    if request.method == 'POST':
        try:
            db = get_db()
            db.execute("""INSERT INTO users (username, email, contacts, passcode, role, business_reg_no, kra_pin, equity_acc) 
                          VALUES (?,?,?,?,?,?,?,?)""",
                       (request.form['username'], request.form['email'], request.form['contacts'], 
                        request.form['password'], request.form['role'], request.form.get('business_reg_no', ''),
                        request.form.get('kra_pin', ''), request.form.get('equity_account', '')))
            db.commit()
            session.pop('terms_accepted', None)
            flash("Identity Verified. Banking Details Linked.")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Registration Error: {str(e)}")
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=?", (request.form['username'],)).fetchone()
        if user and user['passcode'] == request.form['password']:
            session['username'] = user['username']
            session['role'] = user['role']
            session['is_admin'] = user['is_admin']
            return redirect(url_for('dashboard'))
        flash("Access Denied: Invalid Credentials")
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('portal'))

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    search_query = request.args.get('q', '')
    if search_query:
        jobs = db.execute("SELECT * FROM jobs WHERE status='active' AND (title LIKE ? OR skills_required LIKE ?)", ('%'+search_query+'%', '%'+search_query+'%')).fetchall()
    else:
        jobs = db.execute("SELECT * FROM jobs WHERE status='active'").fetchall()
    user = db.execute("SELECT * FROM users WHERE username=?", (session['username'],)).fetchone()
    return render_template('dashboard.html', jobs=jobs, user=user, q=search_query)

@app.route('/jobs')
@login_required
def jobs():
    db = get_db()
    jobs = db.execute("SELECT * FROM jobs WHERE status='active'").fetchall()
    return render_template('jobs.html', jobs=jobs)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    db = get_db()
    if request.method == 'POST':
        db.execute("UPDATE users SET location=?, bio_or_company=? WHERE username=?",
                   (request.form['location'], request.form['bio_or_company'], session['username']))
        db.commit()
        flash("Profile Data Updated.")
        return redirect(url_for('profile'))
    user = db.execute("SELECT * FROM users WHERE username=?", (session['username'],)).fetchone()
    return render_template('profile.html', user=user)

@app.route('/post_job', methods=['GET', 'POST'])
@login_required
def post_job():
    if request.method == 'POST':
        db = get_db()
        db.execute("""INSERT INTO jobs (title, description, salary, poster, location, skills_required, deadline, job_contacts) 
                      VALUES (?,?,?,?,?,?,?,?)""",
                   (request.form['title'], request.form.get('description', ''), request.form['salary'], session['username'],
                    request.form.get('location', ''), request.form.get('skills_required', ''), 
                    request.form.get('deadline', ''), request.form.get('job_contacts', '')))
        db.commit()
        flash("Protocol Broadcast: Job listed on Matrix.")
        return redirect(url_for('dashboard'))
    return render_template('post_job.html')

@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply_job(job_id):
    if session.get('role') != 'employee': 
        flash("Restricted to Employee Class.")
        return redirect(url_for('dashboard'))
    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if request.method == 'POST':
        db.execute("""INSERT INTO applications (job_id, applicant_username, full_name, age, gender, phone, email, photo_url, skills, documents_url) 
                      VALUES (?,?,?,?,?,?,?,?,?,?)""",
                   (job_id, session['username'], request.form['full_name'], request.form['age'],
                    request.form.get('gender'), request.form['phone'], request.form['email'],
                    request.form.get('photo_url'), request.form['skills'], request.form.get('documents_url')))
        db.commit()
        db.execute("UPDATE users SET skills=? WHERE username=?", (request.form['skills'], session['username']))
        db.commit()
        return redirect(url_for('apply_success'))
    return render_template('apply_job.html', job=job)

@app.route('/apply_success')
@login_required
def apply_success():
    return render_template('apply_success.html')

@app.route('/chat/<room_id>', methods=['GET', 'POST'])
@login_required
def chat(room_id):
    db = get_db()
    if request.method == 'POST':
        db.execute("INSERT INTO messages (room_id, sender, text) VALUES (?,?,?)",
                   (room_id, session['username'], request.form['message']))
        db.commit()
        return redirect(url_for('chat', room_id=room_id))
    chats = db.execute("SELECT * FROM messages WHERE room_id=? ORDER BY timestamp ASC", (room_id,)).fetchall()
    return render_template('chat.html', chats=chats, room_id=room_id)

@app.route('/history')
@login_required
def history():
    db = get_db()
    transactions = db.execute("SELECT * FROM transactions WHERE sender=? OR receiver=? ORDER BY timestamp DESC", (session['username'], session['username'])).fetchall()
    return render_template('history.html', transactions=transactions)

# ==============================
# M-PESA DARAJA API ROUTES
# ==============================

@app.route('/mpesa/stkpush', methods=['POST'])
@login_required
def mpesa_stkpush():
    """
    Initiates an M-Pesa payment prompt (STK Push).
    This is what happens when you click 'PAY VIA MPESA' on dashboard.
    """
    if not daraja:
        flash("API ERROR: Safaricom Keys not configured.")
        return redirect(url_for('dashboard'))

    phone = request.form.get('phone')
    amount = request.form.get('amount')
    
    # Format phone: 07... -> 2547...
    if phone.startswith('0'):
        phone = '254' + phone[1:]

    try:
        # Call Daraja
        # IMPORTANT: callback_url MUST be reachable by Safaricom (Not localhost)
        response = daraja.stk_push(
            phone=phone,
            amount=amount,
            callback_url="https://your-domain.com/mpesa/callback", # CHANGE THIS
            account_reference="UTE_JOB_PAYMENT",
            transaction_desc="Salary Payment via UTE-WEB",
            transaction_type="CustomerPayBillOnline"
        )
        
        if response.response_code == '0':
            flash("M-Pesa Prompt Sent to Phone. Enter your PIN to proceed.")
        else:
            flash(f"Payment Failed: {response.response_description}")
            
    except Exception as e:
        flash(f"API Connection Error: {str(e)}")
        
    return redirect(url_for('dashboard'))

@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """
    This is where Safaricom sends the result after user enters PIN.
    """
    data = request.get_json()
    
    # Parse the nested Safaricom JSON
    # Structure: Body -> stkCallback
    body = data.get('Body', {})
    callback = body.get('stkCallback', {})
    result_code = callback.get('ResultCode')
    
    if result_code == '0': # Success
        # Extract metadata
        metadata = callback.get('CallbackMetadata', {})
        items = metadata.get('Item', [])
        
        amount = 0
        mpesa_receipt = ""
        phone = ""
        
        for item in items:
            name = item.get('Name')
            value = item.get('Value')
            if name == 'Amount':
                amount = value
            elif name == 'MpesaReceiptNumber':
                mpesa_receipt = value
            elif name == 'PhoneNumber':
                phone = value

        # --- LOGIC TO PROCESS THE PAYMENT ---
        # Run the Prestige Math
        is_first = True # Logic to determine this based on user history could go here
        split = calculate_prestige_split(amount, is_first)
        
        db = get_db()
        # Log the transaction
        db.execute("""INSERT INTO transactions (sender, receiver, amount, type) 
                      VALUES (?, ?, ?, ?)""",
                   (phone, 'SYSTEM_TREASURY', split['treasury_total'], 'MPESA_DEPOSIT'))
        db.commit()
        
        print(f"PAYMENT SUCCESS: KES {amount} from {phone}")
        
    return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200

# ==============================
# ADMIN PANEL ROUTES
# ==============================

@app.route('/admin_chamber')
@super_admin_required
def admin_panel():
    db = get_db()
    users_count = db.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
    pending_businesses = db.execute("SELECT * FROM users WHERE role='employer' AND is_verified_business=0").fetchall()
    
    # Get all admins to manage them
    all_admins = db.execute("SELECT * FROM users WHERE is_admin=1").fetchall()
    
    return render_template('admin_pannel.html', users_count=users_count, pending_businesses=pending_businesses, all_admins=all_admins)

@app.route('/admin/verify_business/<int:user_id>', methods=['POST'])
@super_admin_required
def verify_business(user_id):
    db = get_db()
    db.execute("UPDATE users SET is_verified_business=1 WHERE id=?", (user_id,))
    db.commit()
    flash("Business Verified.")
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_user/<target_user>', methods=['POST'])
@super_admin_required
def delete_user(target_user):
    db = get_db()
    
    if target_user == 'REUBEN' and session['username'] != 'REUBEN':
        flash("CRITICAL ALERT: ATTEMPT TO DELETE SUPER-ADMIN DETECTED. YOUR ACCOUNT HAS BEEN DISMANTLED.")
        db.execute("DELETE FROM users WHERE username=?", (session['username'],))
        db.commit()
        session.clear()
        return redirect(url_for('portal'))

    db.execute("DELETE FROM users WHERE username=?", (target_user,))
    db.commit()
    flash(f"User {target_user} removed from system.")
    return redirect(url_for('admin_panel'))

@app.route('/admin/promote_admin', methods=['POST'])
@super_admin_required
def promote_admin():
    db = get_db()
    username = request.form['username']
    db.execute("UPDATE users SET is_admin=1, is_verified_business=1 WHERE username=?", (username,))
    db.commit()
    flash(f"User {username} promoted to Admin.")
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
