import os
import sqlite3
import ute
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "RW_PRESTIGE_SUPERMAX_2026"

def get_db():
    conn = sqlite3.connect(ute.DB)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/apply/<int:job_id>')
def apply(job_id):
    if 'username' not in session: return redirect(url_for('login'))
    db = get_db()
    # Create the application
    db.execute("INSERT INTO applications (job_id, applicant) VALUES (?,?)", (job_id, session['username']))
    # Generate Chat Room ID (Job ID + Employer Name + Applicant Name)
    job = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    room_id = f"chat_{job_id}_{job['poster']}_{session['username']}"
    db.commit()
    flash("Applied! Start communicating with the poster below.")
    return redirect(url_for('chat', room_id=room_id))

@app.route('/chat/<room_id>', methods=['GET', 'POST'])
def chat(room_id):
    db = get_db()
    if request.method == 'POST':
        msg = request.form.get('message')
        db.execute("INSERT INTO messages (room_id, sender, text) VALUES (?,?,?)", (room_id, session['username'], msg))
        db.commit()
    
    chats = db.execute("SELECT * FROM messages WHERE room_id=? ORDER BY timestamp ASC", (room_id,)).fetchall()
    return render_template('chat.html', chats=chats, room_id=room_id)

@app.route('/pay_salary', methods=['POST'])
def pay_salary():
    # THE REVENUE ENGINE
    emp_acc = request.form.get('emp_acc')
    gross = float(request.form.get('amount'))
    is_first = request.form.get('is_first') == 'true'
    
    # Run the UTE Formula
    results = ute.calculate_prestige_split(gross, is_first)
    
    # 1. Deduct from Employer Bank (Simulated Jenga Call)
    # 2. Add 'Employee_net' to Employee
    # 3. Add 'Employer_rebate' to Employer
    # 4. Add 'Treasury_total' to YOUR Equity Account
    
    flash(f"Success! Treasury Earned: {results['treasury_total']} KES")
    return redirect(url_for('admin_panel'))

@app.route('/terms')
def terms():
    return """
    <h1>RW Prestige Network: Terms & Conditions</h1>
    <p>1. Registration: A non-refundable fee of 100 KES applies to all members.</p>
    <p>2. Transaction Fees: A 3% ecosystem fee applies to all fund movements.</p>
    <p>3. Revenue Sharing: Employers receive a 10% rebate on first-month placements and 2% monthly thereafter.</p>
    <p>4. Compliance: All users must provide a valid KRA PIN for Equity Bank settlement.</p>
    """

if __name__ == '__main__':
    ute.init_db()
    app.run(host='0.0.0.0', port=10000)
