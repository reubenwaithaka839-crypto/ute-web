from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
import requests
from ute import calculate_prestige_split 

app = Flask(__name__)
# --- CONFIGURATION ---
# Uses Environment Variable on Render, falls back to hardcoded for local
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "RW_SUPERMAX_SECRET_2026")

# DATABASE PATH (Simple and Robust)
DB_PATH = os.environ.get("DB_PATH", "rw_prestige_final.db")

# --- INTASEND API CONFIGURATION ---
INTASEND_API_KEY = "ISSecretKey_test_a659ccb8-316c-4a4c-8e83-e4890fbb90ba"
INTASEND_URL = "https://api.intasend.com/api/v1/payment-request/"

# RENDER CONFIGURATION
base_url = os.environ.get("RENDER_EXTERNAL_URL", "http://127.0.0.1:5000")
CALLBACK_URL = f"{base_url}/mpesa/callback"

# --- DATABASE INITIALIZATION ---
def force_init_db():
    # Get absolute path
    db_file = os.path.abspath(DB_PATH)
    
    # Connect and Create Tables
    conn = sqlite3.connect(db_file)
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

    # SECURITY LOGS TABLE
    # Logs unauthorized attempts to access admin areas
    cur.execute("""CREATE TABLE IF NOT EXISTS security_logs (
        id INTEGER PRIMARY KEY, username TEXT, action TEXT, details TEXT, 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    
    # HARDCODED GOD ADMIN
    # NOTE: The password is CASE-SENSITIVE. 
    # This user is the only one who can create other admins.
    cur.execute("INSERT OR IGNORE INTO users (username, passcode, role, is_admin, is_verified_business) VALUES (?, ?, ?, 1, 1)",
               ('REUBEN', 'I LOVE MY MOTHER 20071975OCTDEC', 'admin'))
    conn.commit()
    conn.close()

force_init_db()

# --- HELPERS ---
def get_db():
    conn = sqlite3.connect(os.path.abspath(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    def wrap(*args, **kwargs):
        if 'username' not in session: return redirect(url_for('portal'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

def super_admin_required(f):
    """
    Restricts access to 'REUBEN' only.
    Logs the attempt if anyone else tries to access the route.
    """
    def wrap(*args, **kwargs):
        if 'username' not in session: 
            return redirect(url_for('portal'))
        
        if session['username'] != 'REUBEN':
            # SPY PROTOCOL: Log the unauthorized attempt
            try:
                db = get_db()
                db.execute("INSERT INTO security_logs (username, action, details) VALUES (?, ?, ?)",
                           (session['username'], 'UNAUTHORIZED_ADMIN_ACCESS', 'Attempted to access Super Admin Chamber'))
                db.commit()
                db.close()
            except:
                pass # Fail silently if logging fails to avoid alerting the hacker
            
            flash("CRITICAL SECURITY ALERT: Your attempt has been logged and reported to REUBEN.")
            return redirect(url_for('dashboard'))
            
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

# --- ROUTES ---

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
            role_input = request.form.get('role', 'employee')
            
            # SECURITY BLOCK: No one can register as 'admin' directly
            # Only 'employer' or 'employee' allowed during registration
            if role_input == 'admin':
                role_input = 'employee' # Force downgrade
                flash("System Alert: Direct Admin Registration is prohibited. Account created as Employee.")

            db = get_db()
            db.execute("""INSERT INTO users (username, email, contacts, passcode, role, business_reg_no, kra_pin, equity_acc) 
                          VALUES (?,?,?,?,?,?,?,?)""",
                       (request.form['username'], request.form['email'], request.form['contacts'], 
                        request.form['password'], role_input, request.form.get('business_reg_no', ''),
                        request.form.get('kra_pin', ''), request.form.get('equity_account', '')))
            db.commit()
            session.pop('terms_accepted', None)
            flash("Identity Verified. System Access Granted.")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Registration Error: {str(e)}")
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            db = get_db()
            user = db.execute("SELECT * FROM users WHERE username=?", (request.form['username'],)).fetchone()
            
            if user and user['passcode'] == request.form['password']:
                session['username'] = user['username']
                session['role'] = user['role']
                session['is_admin'] = user['is_admin']
                return redirect(url_for('dashboard'))
            
            flash("Access Denied: Invalid Credentials")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"System Error: {str(e)}")
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

# --- INTASEND MPESA ROUTES ---

@app.route('/mpesa/stkpush', methods=['POST'])
@login_required
def mpesa_stkpush():
    """Initiates M-Pesa STK Push via IntaSend."""
    phone = request.form.get('phone')
    amount = request.form.get('amount')
    
    # Format phone: 07... -> 2547...
    if phone.startswith('0'):
        phone = '254' + phone[1:]

    # IntaSend Payload
    payload = {
        "api_key": INTASEND_API_KEY,
        "amount": int(amount),
        "phone_number": phone,
        "transaction_reference": "UTE_JOB_PAYMENT",
        "callback_url": CALLBACK_URL
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(INTASEND_URL, json=payload, headers=headers)
        data = response.json()

        if data.get('status') == 'Success' or data.get('status') == 'Success (Test)':
            flash("M-Pesa Prompt Sent! Check your phone and enter PIN.")
        else:
            error_msg = data.get('message', data.get('status', 'Unknown Error'))
            flash(f"Payment Failed: {error_msg}")
            
    except Exception as e:
        flash(f"Connection Error: {str(e)}")
        
    return redirect(url_for('dashboard'))

@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """Receives notification from IntaSend when payment is complete."""
    data = request.get_json()
    print("IntaSend Callback Data:", data)

    if data.get('status') == 'success' or data.get('status') == 'Success':
        amount = data.get('amount')
        phone = data.get('phone_number')
        receipt = data.get('transaction_reference')

        db = get_db()
        db.execute("INSERT INTO transactions (sender, receiver, amount, type) VALUES (?, ?, ?, ?)",
                   (str(phone), 'SYSTEM_TREASURY', amount, 'MPESA_DEPOSIT'))
        db.commit()
        print(f"Transaction Confirmed: KES {amount} from {phone}")
        
    return jsonify({"ResultCode": 0}), 200

# --- GOD ADMIN ROUTES ---

@app.route('/admin_chamber')
@super_admin_required
def admin_panel():
    db = get_db()
    users_count = db.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
    pending_businesses = db.execute("SELECT * FROM users WHERE role='employer' AND is_verified_business=0").fetchall()
    all_admins = db.execute("SELECT * FROM users WHERE is_admin=1").fetchall()
    
    # SECURITY LOGS: Show who tried to access admin
    security_alerts = db.execute("SELECT * FROM security_logs ORDER BY timestamp DESC LIMIT 20").fetchall()

    # List of non-admins available to be promoted
    potential_admins = db.execute("SELECT * FROM users WHERE is_admin=0 AND username != 'REUBEN'").fetchall()
    
    return render_template('admin_pannel.html', 
                          users_count=users_count, 
                          pending_businesses=pending_businesses, 
                          all_admins=all_admins,
                          security_alerts=security_alerts,
                          potential_admins=potential_admins)

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
        # This block is theoretically unreachable due to decorator, but kept for safety
        flash("CRITICAL ALERT: ATTEMPT TO DELETE SUPER-ADMIN DETECTED.")
        return redirect(url_for('admin_panel'))

    db.execute("DELETE FROM users WHERE username=?", (target_user,))
    db.commit()
    flash(f"User {target_user} removed from system.")
    return redirect(url_for('admin_panel'))

@app.route('/admin/grant_admin_access', methods=['POST'])
@super_admin_required
def grant_admin_access():
    """
    REUBEN uses this to manually create a new admin.
    He selects the user and sets their password manually.
    """
    db = get_db()
    username = request.form.get('username')
    new_password = request.form.get('new_password')
    
    if username and new_password:
        db.execute("UPDATE users SET is_admin=1, passcode=?, is_verified_business=1 WHERE username=?",
                   (new_password, username))
        db.commit()
        flash(f"User {username} has been promoted to ADMIN. Password set manually.")
    else:
        flash("Error: Username and Password are required.")
        
    return redirect(url_for('admin_panel'))

@app.route('/admin/dismantle_admin/<target_user>', methods=['POST'])
@super_admin_required
def dismantle_admin(target_user):
    """
    Reuben can remove admin status from a user without deleting their account.
    """
    db = get_db()
    if target_user == 'REUBEN':
        flash("You cannot dismantle the God Admin.")
        return redirect(url_for('admin_panel'))
        
    db.execute("UPDATE users SET is_admin=0 WHERE username=?", (target_user,))
    db.commit()
    flash(f"User {target_user} has been stripped of Admin powers.")
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
