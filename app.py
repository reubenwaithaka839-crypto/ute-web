from flask import Flask, request, redirect, session
from ute import UTE
import bcrypt

app = Flask(__name__)
app.secret_key = "UTE_SUPER_SECURE_2026"

ute = UTE()

# ================= HOME =================
@app.route("/")
def home():
    return """
    <html>
    <body style="font-family:Arial;text-align:center;background:linear-gradient(to right,#0f2027,#203a43,#2c5364);color:white;">
        <h1 style="margin-top:80px;">WELCOME TO UTE</h1>
        <p>Smart Employment + Financial System</p>
        <a href="/auth"><button style="padding:15px 30px;background:#00c6ff;border:none;border-radius:10px;">Get Started</button></a>
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
            return "You must accept Terms & Conditions"

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
    <body style="font-family:Arial;text-align:center;background:#111;color:white;">
        <h1>{role.upper()} DASHBOARD</h1>
        <h2>Welcome {user}</h2>

        <div style="background:#222;padding:20px;margin:20px;border-radius:10px;">
            <h3>Wallet Balance</h3>
            <h2 style="color:#00c6ff;">KES {balance}</h2>
        </div>

        <a href="/wallet"><button>Wallet</button></a>
        <a href="/deposit"><button>Deposit</button></a>
        <a href="/withdraw"><button>Withdraw</button></a>
        <a href="/pay"><button>Send Payment</button></a>

        { '<a href="/admin"><button>Admin Dashboard</button></a>' if role == "admin" else '' }

        <br><br>
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
    <body style="font-family:Arial;text-align:center;background:#222;color:white;">
        <h1>Wallet</h1>
        <h2>KES {balance}</h2>

        <a href="/deposit"><button>Deposit +1000</button></a>
        <a href="/withdraw"><button>Withdraw</button></a>
        <a href="/dashboard"><button>Back</button></a>
    </body>
    </html>
    """

# ================= DEPOSIT =================
@app.route("/deposit")
def deposit():
    if "user" not in session:
        return redirect("/auth")

    ute.update_balance(session["user"], 1000)
    return redirect("/wallet")

# ================= WITHDRAW =================
@app.route("/withdraw", methods=["GET", "POST"])
def withdraw():
    if "user" not in session:
        return redirect("/auth")

    user = session["user"]

    if request.method == "POST":
        amount = int(request.form.get("amount"))
        success = ute.withdraw(user, amount)

        if success:
            return redirect("/wallet")
        return "Insufficient Balance"

    return """
    <html>
    <body style="text-align:center;font-family:Arial;background:#111;color:white;">
        <h1>Withdraw</h1>
        <form method="POST">
            <input name="amount" placeholder="Amount">
            <button type="submit">Withdraw</button>
        </form>
    </body>
    </html>
    """

# ================= PAYMENTS =================
@app.route("/pay", methods=["GET", "POST"])
def pay():
    if "user" not in session:
        return redirect("/auth")

    sender = session["user"]

    if request.method == "POST":
        receiver = request.form.get("receiver")
        amount = int(request.form.get("amount"))

        success = ute.transfer_with_commission(sender, receiver, amount)

        if success:
            return redirect("/wallet")
        return "Payment Failed"

    return """
    <html>
    <body style="text-align:center;font-family:Arial;background:#111;color:white;">
        <h1>Send Payment</h1>

        <form method="POST">
            <input name="receiver" placeholder="Receiver Username"><br><br>
            <input name="amount" placeholder="Amount"><br><br>
            <button type="submit">Send</button>
        </form>
    </body>
    </html>
    """

# ================= ADMIN DASHBOARD =================
@app.route("/admin")
def admin():
    if "user" not in session or session["role"] != "admin":
        return "Access Denied"

    users = ute.get_total_users()
    total = ute.get_total_system_balance()
    earnings = ute.get_admin_earnings()

    return f"""
    <html>
    <body style="font-family:Arial;text-align:center;background:#0d0d0d;color:white;">
        <h1>ADMIN DASHBOARD</h1>

        <h2>Total Users: {users}</h2>
        <h2>Total System Balance: KES {total}</h2>
        <h2>Admin Earnings: KES {earnings}</h2>

        <a href="/dashboard"><button>Back</button></a>
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
