from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import ute
import os

app = Flask(__name__)
app.secret_key = "RW_SUPERMAX_SECRET_2026"

def get_db():
    conn = sqlite3.connect(ute.DB)
    conn.row_factory = sqlite3.Row
    return conn

# --- PROTECTION DECORATORS ---
def login_required(f):
    def wrap(*args, **kwargs):
        if 'username' not in session: return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

def employer_verified_required(f):
    def wrap(*args, **kwargs):
        if session.get('role') != 'employer': return redirect(url_for('dashboard'))
        db = get_db()
        user = db.execute("SELECT is_verified_business FROM users WHERE username=?", (session['username'],)).fetchone()
        if not user or user['is_verified_business'] != 1:
            flash("Access Denied: Your business registration is pending admin verification.")
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
    if not session.get('terms_accepted'):
        return redirect(url_for('terms'))
    
    if request.method == 'POST':
        db = get_db()
        reg_no = request.form.get('business_reg_no', '')
        
        try:
            db.execute("""INSERT INTO users (username, email, contacts, passcode, role, business_reg_no) 
                          VALUES (?,?,?,?,?,?)""",
                       (request.form['username'], request.form['email'], request.form['contacts'], 
                        request.form['password'], request.form['role'], reg_no))
            db.commit()
            session.pop('terms_accepted', None)
            flash("Identity registered. Awaiting login.")
            return redirect(url_for('login'))
        except Exception as e:
            flash("Error: Identity already exists or invalid data.")
            return redirect(url_for('register')) # FIX: Prevents ERR_CACHE_MISS
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
        return redirect(url_for('login')) # FIX: Prevents ERR_CACHE_MISS
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('portal'))

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    jobs = db.execute("SELECT * FROM jobs WHERE status='active'").fetchall()
    user = db.execute("SELECT * FROM users WHERE username=?", (session['username'],)).fetchone()
    return render_template('dashboard.html', jobs=jobs, user=user)

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
        flash("Profile Updated")
        return redirect(url_for('profile'))
    user = db.execute("SELECT * FROM users WHERE username=?", (session['username'],)).fetchone()
    return render_template('profile.html', user=user)

# EMPLOYER ROUTES (PROTECTED)
@app.route('/post_job', methods=['GET', 'POST'])
@employer_verified_required
def post_job():
    if request.method == 'POST':
        db = get_db()
        db.execute("INSERT INTO jobs (title, description, salary, poster) VALUES (?,?,?,?)",
                   (request.form['title'], request.form.get('description', 'No description'), request.form['salary'], session['username']))
        db.commit()
        flash("Job listed successfully.")
        return redirect(url_for('dashboard'))
    return render_template('post_job.html')

@app.route('/view_applicants/<int:job_id>')
@employer_verified_required
def view_applicants(job_id):
    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    applicants = db.execute("SELECT * FROM applications WHERE job_id=?", (job_id,)).fetchall()
    return render_template('view_aplicants.html', job=job, applicants=applicants)

@app.route('/talents')
@employer_verified_required
def talents():
    db = get_db()
    workers = db.execute("SELECT * FROM users WHERE role='employee' AND skills IS NOT NULL AND skills != ''").fetchall()
    return render_template('talents.html', workers=workers)

# EMPLOYEE ROUTES
@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply_job(job_id):
    if session.get('role') != 'employee': return redirect(url_for('dashboard'))
    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    
    if request.method == 'POST':
        db.execute("""INSERT INTO applications (job_id, applicant_username, full_name, age, gender, phone, email, photo_url, skills) 
                      VALUES (?,?,?,?,?,?,?,?,?)""",
                   (job_id, session['username'], request.form['full_name'], request.form['age'],
                    request.form.get('gender'), request.form['phone'], request.form['email'],
                    request.form.get('photo_url'), request.form['skills']))
        db.commit()
        
        # Update user profile with skills so they show up in talents.html
        db.execute("UPDATE users SET skills=? WHERE username=?", (request.form['skills'], session['username']))
        db.commit()
        
        return redirect(url_for('apply_success'))
    return render_template('apply_job.html', job=job)

@app.route('/apply_success')
def apply_success():
    return render_template('apply_success.html')

# CHAT ROUTES
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

# HISTORY & LEDGER
@app.route('/history')
@login_required
def history():
    db = get_db()
    transactions = db.execute("SELECT * FROM transactions WHERE sender=? OR receiver=? ORDER BY timestamp DESC", (session['username'], session['username'])).fetchall()
    return render_template('history.html', transactions=transactions)

@app.route('/ledger')
@login_required
def ledger():
    db = get_db()
    # Mock history data for ledger structure
    history = []
    return render_template('ledger.html', history=history)

# PAYMENT ROUTE (Prevents 404 errors on payment page)
@app.route('/process_payment', methods=['POST'])
def process_payment():
    try:
        # Requires IntaSend keys in Render Environment Variables to actually process
        return {"success": False, "error": "Payment API keys not configured in Render environment yet."}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ADMIN ROUTES
@app.route('/admin_chamber')
def admin_panel():
    if session.get('username') != 'REUBEN': return "Unauthorized", 403
    db = get_db()
    users_count = db.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
    pending_businesses = db.execute("SELECT * FROM users WHERE role='employer' AND is_verified_business=0").fetchall()
    return render_template('admin_pannel.html', users_count=users_count, pending_businesses=pending_businesses)

@app.route('/admin/manage_admins', methods=['POST'])
def manage_admins():
    if session.get('username') != 'REUBEN': return "Unauthorized", 403
    db = get_db()
    action = request.form['action']
    target = request.form['target_user']
    
    if action == 'promote':
        db.execute("UPDATE users SET is_admin=1, is_verified_business=1 WHERE username=?", (target,))
    elif action == 'dismantle':
        db.execute("UPDATE users SET is_admin=0 WHERE username=?", (target,))
    
    db.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/verify_business/<int:user_id>', methods=['POST'])
def verify_business(user_id):
    if session.get('username') != 'REUBEN': return "Unauthorized", 403
    db = get_db()
    db.execute("UPDATE users SET is_verified_business=1 WHERE id=?", (user_id,))
    db.commit()
    flash("Business Verified Successfully.")
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    ute.init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
