import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'reubbie_profile_v12')

DB = "ute_supermax_FINAL_BOSS_V12.db"

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, role TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, location TEXT, salary REAL, posted_by TEXT, fee_paid INTEGER DEFAULT 0)")
    # UPDATED: Added photo_url
    cur.execute("""CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        job_id INTEGER, 
        applicant_username TEXT,
        full_name TEXT,
        id_number TEXT,
        phone TEXT,
        email TEXT,
        gender TEXT,
        age INTEGER,
        location TEXT,
        skills TEXT,
        photo_url TEXT,
        status TEXT DEFAULT 'pending'
    )""")
    cur.execute(query, args)
    if commit: conn.commit()
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/submit_application', methods=['POST'])
def submit_application():
    if 'username' not in session: return redirect(url_for('login'))
    
    # Collect all data including the Photo Link
    j_id = request.form.get('job_id')
    fn = request.form.get('full_name')
    idn = request.form.get('id_number')
    ph = request.form.get('phone')
    em = request.form.get('email')
    gen = request.form.get('gender')
    age = request.form.get('age')
    loc = request.form.get('location')
    skl = request.form.get('skills')
    photo = request.form.get('photo_url') # New Field

    query_db("""INSERT INTO applications 
        (job_id, applicant_username, full_name, id_number, phone, email, gender, age, location, skills, photo_url) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
        (j_id, session['username'], fn, idn, ph, em, gen, age, loc, skl, photo), commit=True)
    
    return redirect(url_for('index'))

# --- VIEW APPLICANTS (For Employers) ---
@app.route('/view_applicants/<int:job_id>')
def view_applicants(job_id):
    job = query_db("SELECT * FROM jobs WHERE id = ?", (job_id,), one=True)
    # Ensure only the owner of the job can see who applied
    if job['posted_by'] != session['username'] and session['role'] != 'admin':
        return "Unauthorized", 403
        
    applicants = query_db("SELECT * FROM applications WHERE job_id = ?", (job_id,))
    return render_template('view_applicants.html', job=job, applicants=applicants)

# ... (Keep existing routes)
