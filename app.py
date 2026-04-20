from flask import Flask, request, redirect, session, render_template, url_for
import sqlite3, ute, mpesa, os, bcrypt

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "UTE_FINAL_REMEDY_2026")

@app.route("/")
def index():
    return redirect(url_for("auth")) if "user" not in session else redirect(url_for("dashboard"))

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        # 1. Grab every single field from your HTML
        un = request.form.get("username")
        em = request.form.get("email")
        ph = request.form.get("phone")
        ni = request.form.get("national_id")
        pw = request.form.get("password")
        ro = request.form.get("role")
        lo = request.form.get("location", "Nairobi") # Default if empty
        sk = request.form.get("skills", "General")   # Default if empty

        # 2. Safety Check: Don't allow empty critical fields
        if not all([un, em, ph, ni, pw]):
            return "Error: All fields (Username, Email, Phone, National ID, Password) are required."

        hashed = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())
        
        conn = sqlite3.connect(ute.DB)
        try:
            # 3. Try to insert
            conn.execute("""INSERT INTO users (username, email, phone, national_id, password, role, location, skills) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                         (un, em, ph, ni, hashed, ro, lo, sk))
            
            # 4. Create the wallet immediately
            conn.execute("INSERT OR IGNORE INTO wallet (username, balance) VALUES (?, 0)", (un,))
            conn.commit()
            
            session.update({"user": un, "role": ro, "phone": ph, "email": em})
            return redirect(url_for("dashboard"))

        except sqlite3.IntegrityError as e:
            # THIS IS THE CRITICAL PART: It tells us which field is the duplicate
            return f"Clash Detected: One of your details (Email, Phone, or ID) is already in the system. Technical detail: {e}"
        except Exception as e:
            return f"System Error: {e}"
        finally:
            conn.close()
    return render_template("auth.html")

# Keep the rest of your app.py routes (dashboard, pay, etc.) as they were
