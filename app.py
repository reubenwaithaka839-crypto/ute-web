from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import ute
import os

app = Flask(__name__)
app.secret_key = "SUPERMAX_SECRET_RW"

def get_db():
    conn = sqlite3.connect(ute.DB)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def portal():
    return render_template('portal.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        db = get_db()
        db.execute("INSERT INTO users (username, email, contacts, passcode, role) VALUES (?,?,?,?,?)",
                   (request.form['username'], request.form['email'], request.form['contacts'], 
                    request.form['password'], request.form['role']))
        db.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/apply/<int:job_id>')
def apply(job_id):
    if 'username' not in session: return redirect(url_for('login'))
    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    room_id = f"chat_{job_id}_{session['username']}"
    
    # AUTO-MESSAGE: System forces employee to send details
    db.execute("INSERT INTO messages (room_id, sender, text) VALUES (?,?,?)", 
               (room_id, 'SYSTEM', f"Application started for {job['title']}. Please upload your photo and bank details."))
    db.commit()
    return redirect(url_for('chat', room_id=room_id))

@app.route('/admin/manage_admins', methods=['POST'])
def manage_admins():
    if session.get('username') != 'REUBEN': return "Access Denied", 403
    target = request.form['target_user']
    action = request.form['action'] # 'promote' or 'dismantle'
    val = 1 if action == 'promote' else 0
    db = get_db()
    db.execute("UPDATE users SET is_admin=? WHERE username=?", (val, target))
    db.commit()
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    ute.init_db()
    app.run(host='0.0.0.0', port=10000)
