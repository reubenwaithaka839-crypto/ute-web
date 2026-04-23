import os
import sqlite3
import ute
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', "RW_PRESTIGE_SUPERMAX_2026")
bcrypt = Bcrypt(app)

def get_db():
    conn = sqlite3.connect(ute.DB)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('portal.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        
        db = get_db()
        try:
            db.execute("INSERT INTO users (username, passcode, role) VALUES (?, ?, ?)", (username, hashed_pw, role))
            db.commit()
            flash("Registration Successful! Please Login.", "success")
            return redirect(url_for('login'))
        except:
            flash("Username taken.", "red")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and bcrypt.check_password_hash(user['passcode'], password):
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        flash("Invalid Credentials", "red")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session: return redirect(url_for('login'))
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username=?", (session['username'],)).fetchone()
    jobs = db.execute("SELECT * FROM jobs").fetchall()
    return render_template('dashboard.html', user=user, jobs=jobs)

@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if session.get('role') not in ['employer', 'admin']: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        db = get_db()
        db.execute("INSERT INTO jobs (title, salary, poster) VALUES (?, ?, ?)", 
                   (request.form.get('title'), request.form.get('salary'), session['username']))
        db.commit()
        flash("Job Posted Successfully!")
        return redirect(url_for('dashboard'))
    return render_template('post_job.html')

@app.route('/pay_salary', methods=['POST'])
def pay_salary():
    if session.get('role') != 'admin': return "Unauthorized", 403
    
    emp_user = request.form.get('emp_username')
    gross = float(request.form.get('amount'))
    is_first = request.form.get('is_first') == 'true'
    
    results = ute.calculate_prestige_split(gross, is_first)
    
    # Update Database Balances
    db = get_db()
    db.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (results['employee_net'], emp_user))
    db.execute("UPDATE users SET balance = balance + ? WHERE role = 'admin'", (results['treasury_total'],))
    db.commit()
    
    flash(f"Payout Released! Treasury: {results['treasury_total']} KES")
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    ute.init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
