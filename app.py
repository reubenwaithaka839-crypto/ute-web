import sqlite3
import ute
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'RW_ULTIMATE_PRESTIGE_2026_SECURE'
DB = ute.DB

def init_db():
    """Initialize database tables once at startup"""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Create tables
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE, 
        passcode TEXT, 
        email TEXT, 
        role TEXT, 
        bank_name TEXT, 
        acc_number TEXT, 
        holder_name TEXT)""")
    
    cur.execute("CREATE TABLE IF NOT EXISTS blacklist (username TEXT UNIQUE, email TEXT UNIQUE)")
    cur.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, salary REAL, employer TEXT)")
    cur.execute("""CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        job_id INTEGER, 
        applicant TEXT, 
        phone TEXT, 
        email TEXT, 
        age INTEGER, 
        skills TEXT, 
        gender TEXT, 
        photo_url TEXT, 
        status TEXT DEFAULT 'pending')""")
    cur.execute("CREATE TABLE IF NOT EXISTS treasury (account_name TEXT, account_number TEXT, bank_name 
