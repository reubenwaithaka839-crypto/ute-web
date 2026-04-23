from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3, ute, os

app = Flask(__name__)
app.secret_key = "RW_SUPERMAX_SECRET"

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
        try:
            db.execute("INSERT INTO users (username, email, contacts, passcode, role) VALUES (?,?,?,?,?)",
                       (request.form['username'], request.form['email'], request.form['contacts'], 
                        request.form['password'], request.form['role']))
            db.commit()
            flash("Prestige Account Created. Enter Chamber.")
            return redirect(url_for('login'))
        except:
            flash("Username already exists in the network.")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = get_db().execute("SELECT * FROM users WHERE username=?", (request.form['username'],)).fetchone()
        if user and user['passcode'] == request.form['password']:
            session['username'] = user['username']
            session['role'] = user['role']
            session['is_admin'] = user['is_admin']
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/apply/<int:job_id>')
def apply(job_id):
    if 'username' not in session: return redirect(url_for('login'))
    # Immediate Chat Logic
    room_id = f"chat_{job_id}_{session['username']}"
    return redirect(url_for('chat', room_id=room_id))

if __name__ == '__main__':
    ute.init_db()
    app.run(host='0.0.0.0', port=10000)
