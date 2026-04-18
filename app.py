from flask import Flask, request, redirect, session, url_for
from ute import UTE
import bcrypt

app = Flask(__name__)
app.secret_key = "super_secret_key_123"

ute = UTE()

# ================= HOME =================
@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>UTE System</title>
        <style>
            body {
                font-family: Arial;
                background: linear-gradient(to right, #141E30, #243B55);
                color: white;
                text-align: center;
            }
            h1 {margin-top: 80px; font-size: 50px;}
            .btn {
                padding: 15px 30px;
                background: #00c6ff;
                border: none;
                border-radius: 10px;
                font-size: 18px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <h1>Welcome to UTE</h1>
        <p>Smart Employment & Financial Platform</p>
        <a href="/auth"><button class="btn">Get Started</button></a>
    </body>
    </html>
    """

# ================= AUTH =================
@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        name = request.form.get("name")
        password = request.form.get("password")
        role = request.form.get("role")
        agree = request.form.get("agree")

        bank = request.form.get("bank")
        acc_name = request.form.get("acc_name")
        acc_number = request.form.get("acc_number")

        if not agree:
            return "You must agree to Terms"

        if not name or not password:
            return "Missing fields"

        # hash password safely
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # save user
        ute.register_user(name, hashed, role)

        # save bank for non-admin
        if role != "admin":
            ute.save_user_bank(name, role, bank, acc_name, acc_number)

        session["user"] = name
        session["role"] = role

        return redirect("/dashboard")

    return """
    <html>
    <head>
    <style>
    body {font-family: Arial; background:#1e1e2f; color:white;}
    form {
        margin: 50px auto;
        width: 350px;
        background:#2b2b3c;
        padding:20px;
        border-radius:15px;
    }
    input, select {
        width:100%;
        padding:10px;
        margin:10px 0;
        border:none;
        border-radius:5px;
    }
    button {
        padding:10px;
        width:100%;
        background:#00c6ff;
        border:none;
        border-radius:5px;
    }
    </style>
    </head>
    <body>
    <form method="POST">
        <h2>Register / Login</h2>

        <input name="name" placeholder="Name" required>
        <input type="password" name="password" placeholder="Password" required>

        <select name="role">
            <option value="employee">Employee</option>
            <option value="employer">Employer</option>
            <option value="admin">Admin</option>
        </select>

        <input name="bank" placeholder="Bank Name">
        <input name="acc_name" placeholder="Account Name">
        <input name="acc_number" placeholder="Account Number">

        <label>
            <input type="checkbox" name="agree"> Agree to Terms
        </label>

        <button type="submit">Continue</button>
    </form>
    </body>
    </html>
    """

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/auth")

    user = session["user"]
    role = session["role"]

    if role == "admin":
        return f"""
        <html>
        <body style='background:#111;color:white;font-family:Arial;text-align:center'>
        <h1>Admin Dashboard</h1>
        <p>Welcome {user}</p>
        <a href="/admin_bank">Set Bank Details</a><br><br>
        <a href="/logout">Logout</a>
        </body>
        </html>
        """

    elif role == "employer":
        return f"""
        <html>
        <body style='background:#222;color:white;font-family:Arial;text-align:center'>
        <h1>Employer Dashboard</h1>
        <p>Welcome {user}</p>
        <a href="/logout">Logout</a>
        </body>
        </html>
        """

    else:
        return f"""
        <html>
        <body style='background:#333;color:white;font-family:Arial;text-align:center'>
        <h1>Employee Dashboard</h1>
        <p>Welcome {user}</p>
        <a href="/logout">Logout</a>
        </body>
        </html>
        """

# ================= ADMIN BANK =================
@app.route("/admin_bank", methods=["GET", "POST"])
def admin_bank():
    if request.method == "POST":
        bank = request.form.get("bank")
        name = request.form.get("name")
        number = request.form.get("number")

        if not bank or not name or not number:
            return "Fill all fields"

        ute.save_admin_bank(bank, name, number)
        return redirect("/dashboard")

    return """
    <html>
    <body style='font-family:Arial;text-align:center'>
    <h2>Admin Bank Setup</h2>
    <form method="POST">
        <input name="bank" placeholder="Bank Name"><br><br>
        <input name="name" placeholder="Account Name"><br><br>
        <input name="number" placeholder="Account Number"><br><br>
        <button type="submit">Save</button>
    </form>
    </body>
    </html>
    """

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
