import os
import sqlite3
import ute
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'RW_ULTIMATE_GOD_KEY_2026'
DB = ute.DB

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, passcode TEXT, email TEXT, role TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS blacklist (username TEXT UNIQUE, email TEXT UNIQUE)")
    cur.execute(query, args)
    if commit: conn.commit()
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/portal')
def portal():
    return render_template('portal.html')

@app.route('/')
def index():
    if 'username' not in session: return redirect(url_for('portal'))
    if not session.get('terms_accepted'): return redirect(url_for('terms'))
    
    user = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
    if not user:
        session.clear()
        return redirect(url_for('login'))
        
    if user['role'] == 'admin': return redirect(url_for('admin_panel'))
    return render_template('dashboard.html', user=user)

@app.route('/terms', methods=['GET', 'POST'])
def terms():
    if request.method == 'POST':
        session['terms_accepted'] = True
        return redirect(url_for('index'))
    return render_template('terms.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p, e, r = request.form.get('username'), request.form.get('passcode'), request.form.get('email'), request.form.get('role')
        
        is_banned = query_db("SELECT * FROM blacklist WHERE username = ? OR email = ?", (u, e), one=True)
        if is_banned: return "ACCESS DENIED: Identity Dismantled.", 403
        
        role = 'admin' if u.upper() == 'REUBEN' else r
        user = query_db("SELECT * FROM users WHERE username = ?", (u,), one=True)
        if not user:
            query_db("INSERT INTO users (username, passcode, email, role) VALUES (?, ?, ?, ?)", (u, p, e, role), commit=True)
        
        session['username'] = u
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/admin_panel')
def admin_panel():
    if 'username' not in session or session['username'].upper() != 'REUBEN': return "UNAUTHORIZED", 403
    all_users = query_db("SELECT * FROM users")
    return render_template('admin_pannel.html', all_users=all_users)

@app.route('/dismantle_admin/<username>')
def dismantle_admin(username):
    if 'username' not in session or session['username'].upper() != 'REUBEN': return "UNAUTHORIZED", 403
    target = query_db("SELECT * FROM users WHERE username = ?", (username,), one=True)
    if target and username.upper() != 'REUBEN':
        query_db("INSERT INTO blacklist (username, email) VALUES (?, ?)", (target['username'], target['email']), commit=True)
        query_db("DELETE FROM users WHERE username = ?", (username,), commit=True)
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('portal'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
