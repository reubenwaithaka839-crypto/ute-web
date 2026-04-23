import os
import sqlite3
import ute
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', "RW_PRESTIGE_SUPERMAX_2026")

def get_db():
    conn = sqlite3.connect(ute.DB)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('portal.html') # Entrance page

@app.route('/dashboard')
def dashboard():
    if 'username' not in session: return redirect(url_for('home'))
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username=?", (session['username'],)).fetchone()
    jobs = db.execute("SELECT * FROM jobs").fetchall()
    return render_template('dashboard.html', user=user, jobs=jobs)

@app.route('/admin_pannel')
def admin_panel():
    if session.get('role') != 'admin':
        flash("Unauthorized Access.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    users_count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    jobs_count = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    apps_count = db.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    recent_users = db.execute("SELECT * FROM users ORDER BY id DESC LIMIT 10").fetchall()
    
    config = {"bank_status": "ONLINE", "kra_pin": "ACTIVE-SINK"}
    
    return render_template('admin_pannel.html', 
                           users_count=users_count, 
                           jobs_count=jobs_count, 
                           apps_count=apps_count,
                           employers_count="N/A", 
                           recent_users=recent_users, 
                           config=config)

@app.route('/apply/<int:job_id>')
def apply(job_id):
    if 'username' not in session: return redirect(url_for('login'))
    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if job:
        db.execute("INSERT INTO applications (job_id, applicant) VALUES (?,?)", (job_id, session['username']))
        room_id = f"chat_{job_id}_{job['poster']}_{session['username']}"
        db.commit()
        return redirect(url_for('chat', room_id=room_id))
    return "Job not found", 404

@app.route('/chat/<room_id>', methods=['GET', 'POST'])
def chat(room_id):
    if 'username' not in session: return redirect(url_for('login'))
    db = get_db()
    if request.method == 'POST':
        msg = request.form.get('message')
        db.execute("INSERT INTO messages (room_id, sender, text) VALUES (?,?,?)", (room_id, session['username'], msg))
        db.commit()
    
    chats = db.execute("SELECT * FROM messages WHERE room_id=? ORDER BY timestamp ASC", (room_id,)).fetchall()
    return render_template('chat.html', chats=chats, room_id=room_id)

@app.route('/pay_salary', methods=['POST'])
def pay_salary():
    if session.get('role') != 'admin': return "Unauthorized", 403
    
    emp_username = request.form.get('emp_username')
    employer_username = request.form.get('employer_username')
    gross = float(request.form.get('amount'))
    is_first = request.form.get('is_first') == 'true'
    
    # Calculate Splits via UTE
    results = ute.calculate_prestige_split(gross, is_first)
    
    db = get_db()
    try:
        # 1. Update Employee Balance
        db.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (results['employee_net'], emp_username))
        # 2. Update Employer Rebate
        db.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (results['employer_rebate'], employer_username))
        # 3. Update Admin/Treasury (The Admin account usually holds the Treasury)
        db.execute("UPDATE users SET balance = balance + ? WHERE role = 'admin'", (results['treasury_total'],))
        
        db.commit()
        flash(f"Payment Processed! Treasury Cut: {results['treasury_total']} KES")
    except Exception as e:
        db.rollback()
        flash(f"Error: {str(e)}")
        
    return redirect(url_for('admin_panel'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        passcode = request.form.get('passcode')
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=? AND passcode=?", (username, passcode)).fetchone()
        if user:
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        flash("Invalid Credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    ute.init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
