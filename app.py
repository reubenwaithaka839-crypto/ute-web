from flask import Flask, request, redirect, session
from ute import UTE
import bcrypt

app = Flask(__name__)
app.secret_key = "ute_super_secret_key_2026"

ute = UTE()

# ================= HOME =================
@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>UTE Platform</title>
        <style>
            body {
                font-family: Arial;
                background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
                color: white;
                text-align: center;
            }
            h1 { margin-top: 80px; font-size: 50px; }
            .btn {
                padding: 15px 30px;
                background: #00c6ff;
                border: none;
                border-radius: 10px;
                font-size: 18px;
                cursor: pointer;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <h1>Welcome to UTE</h1>
        <p>Employment + Financial System Platform</p>
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
            return "You must accept Terms"

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        ute.register_user(name, hashed, role)

        if role != "admin":
            ute.save_user_bank(name, role, bank, acc_name, acc_number)

        session["user"] = name
        session["role"] = role

        return redirect("/dashboard")

    return """
    <html>
    <body style="font-family:Arial;background:#1e1e2f;color:white;">
    <form method="POST" style="width:350px;margin:50px auto;background:#2b2b3c;padding:20px;border-radius:15px;">
        <h2>Register / Login</h2>

        <input name="name" placeholder="Name" required style="width:100%;padding:10px;margin:10px 0;">
        <input type="password" name="password" placeholder="Password" required style="width:100%;padding:10px;margin:10px 0;">

        <select name="role" style="width:100%;padding:10px;margin:10px 0;">
            <option value="employee">Employee</option>
            <option value="employer">Employer</option>
            <option value="admin">Admin</option>
        </select>

        <input name="bank" placeholder="Bank Name" style="width:100%;padding:10px;margin:10px 0;">
        <input name="acc_name" placeholder="Account Name" style="width:100%;padding:10px;margin:10px 0;">
        <input name="acc_number" placeholder="Account Number" style="width:100%;padding:10px;margin:10px 0;">

        <label><input type="checkbox" name="agree"> I agree to Terms</label>

        <button type="submit" style="width:100%;padding:10px;background:#00c6ff;border:none;margin-top:10px;">Continue</button>
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

    balance = ute.get_balance(user)

    return f"""
    <html>
    <body style="font-family:Arial;background:#111;color:white;text-align:center;">
        <h1>{role.upper()} DASHBOARD</h1>
        <h2>Welcome {user}</h2>

        <div style="background:#222;padding:20px;margin:20px;border-radius:10px;">
            <h3>Wallet Balance</h3>
            <h2 style="color:#00c6ff;">KES {balance}</h2>
        </div>

        <a href="/wallet"><button>Open Wallet</button></a>
        <a href="/deposit"><button>Deposit +1000</button></a>
        <a href="/logout"><button>Logout</button></a>
    </body>
    </html>
    """

# ================= WALLET =================
@app.route("/wallet")
def wallet():
    if "user" not in session:
        return redirect("/auth")

    user = session["user"]
    balance = ute.get_balance(user)

    return f"""
    <html>
    <body style="font-family:Arial;background:#222;color:white;text-align:center;">
        <h1>Wallet</h1>
        <h2>Your Balance: KES {balance}</h2>
        <a href="/deposit"><button>Add 1000</button></a>
        <a href="/dashboard"><button>Back</button></a>
    </body>
    </html>
    """

# ================= DEPOSIT =================
@app.route("/deposit")
def deposit():
    if "user" not in session:
        return redirect("/auth")

    user = session["user"]
    ute.update_balance(user, 1000)

    return redirect("/wallet")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
