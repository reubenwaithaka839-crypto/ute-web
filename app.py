from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from ute import calculate_prestige_split 

app = Flask(__name__)
app.secret_key = "RW_SUPERMAX_SECRET_2026"
DB_PATH = "rw_prestige_final.db"

def force_init_db():
    conn = sqlite3.connect(DB_PATH)
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
    
    # --- HARDC
