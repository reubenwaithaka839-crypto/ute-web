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

# 1. THE ENTRANCE (portal.html)
@app.route('/')
def portal():
    return render_template('portal.html')

# 2. THE LOGIN (login.html)
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
    return render_template('login.html')

# 3. THE REGISTRATION (register.html)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        db = get_db()
        try:
            db.execute("INSERT INTO users (username, email, contacts, passcode, role) VALUES (?,?,?,?,?)",
                       (request.form['username'], request.form['email'], request.form['contacts'], 
                        request.form['password'], request.form['role']))
            db.commit()
            return redirect(url_for('login'))
        except:
            flash("Identity already exists.")
    return render_template('register.html')

# 4. THE DASHBOARD (dashboard.html)
@app.route('/dashboard')
def dashboard():
    if 'username' not in session: return redirect(url_for('login'))
    db = get_db()
    jobs = db.execute("SELECT * FROM jobs").fetchall()
    user = db.execute("SELECT * FROM users WHERE username=?", (session['username'],)).fetchone()
    return render_template('dashboard.html', jobs=jobs, user=user)

# 5. INSTANT CHAT (chat.html)
@app.route('/chat/<room_id>')
def chat(room_id):
    if 'username' not in session: return redirect(url_for('login'))
    db = get_db()
    chats = db.execute("SELECT * FROM messages WHERE room_id=? ORDER BY timestamp ASC", (room_id,)).fetchall()
    return render_template('chat.html', chats=chats, room_id=room_id)

# 6. ADMIN GOD PANEL (admin_pannel.html)
@app.route('/admin_chamber')
def admin_panel():
    if session.get('username') != 'REUBEN': return "Unauthorized", 403
    db = get_db()
    # Stats for the God View
    users = db.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
    return render_template('admin_pannel.html', users_count=users)

if __name__ == '__main__':
    ute.init_db()
    app.run(host='0.0.0.0', port=10000)
