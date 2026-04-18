from flask import Flask, request, jsonify, session, redirect
from ute import UTE
import bcrypt
import joblib
import os

app = Flask(__name__)
app.secret_key = "UTE_PRODUCTION_KEY"

ute = UTE()

# ================= LOAD AI MODEL =================
MODEL_PATH = "fraud_model.pkl"
model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None

# ================= AI FRAUD PREDICTION =================
def predict_fraud(amount, sender, receiver):
    if model is None:
        return 0, 0.0

    self_transfer = 1 if sender == receiver else 0
    prediction = model.predict([[amount, self_transfer]])[0]
    probability = model.predict_proba([[amount, self_transfer]])[0][1]

    return prediction, probability

# ================= AUTH API =================
@app.route("/api/register", methods=["POST"])
def register():
    data = request.json

    name = data["name"]
    password = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt())
    role = data["role"]

    ute.register_user(name, password, role)
    ute.init_wallet(name)

    return jsonify({"status": "success"})

@app.route("/api/login", methods=["POST"])
def login():
    return jsonify({"message": "Use frontend auth or extend DB validation here"})

# ================= WALLET API =================
@app.route("/api/wallet/<user>")
def wallet(user):
    return jsonify({
        "user": user,
        "balance": ute.get_balance(user)
    })

# ================= TRANSFER (WITH AI FRAUD) =================
@app.route("/api/transfer", methods=["POST"])
def transfer():
    data = request.json

    sender = data["sender"]
    receiver = data["receiver"]
    amount = float(data["amount"])

    # AI FRAUD CHECK
    prediction, risk = predict_fraud(amount, sender, receiver)

    if prediction == 1:
        ute.flag_fraud(sender, "AI BLOCKED TRANSACTION", amount)
        return jsonify({
            "status": "blocked",
            "risk_score": risk
        })

    success = ute.transfer_with_commission(sender, receiver, amount)

    return jsonify({
        "status": "success" if success else "failed",
        "risk_score": risk
    })

# ================= PAYROLL API =================
@app.route("/api/payroll/run", methods=["POST"])
def run_payroll():
    ute.run_payroll()
    return jsonify({"status": "payroll_executed"})

# ================= PAYROLL DATA =================
@app.route("/api/payroll")
def payroll():
    return jsonify(ute.get_all_payroll())

# ================= MPESA CALLBACK (LIVE INTEGRATION READY) =================
@app.route("/api/mpesa/callback", methods=["POST"])
def mpesa_callback():
    data = request.json

    try:
        stk = data["Body"]["stkCallback"]
        result_code = stk["ResultCode"]

        metadata = stk.get("CallbackMetadata", {}).get("Item", [])

        phone = None
        amount = None
        receipt = None

        for item in metadata:
            if item["Name"] == "PhoneNumber":
                phone = item["Value"]
            if item["Name"] == "Amount":
                amount = item["Value"]
            if item["Name"] == "MpesaReceiptNumber":
                receipt = item["Value"]

        status = "SUCCESS" if result_code == 0 else "FAILED"

        ute.save_mpesa(phone, amount, status, receipt)

        return jsonify({"Result": "OK"})

    except Exception as e:
        return jsonify({"error": str(e)})

# ================= FRAUD DASHBOARD API =================
@app.route("/api/fraud")
def fraud():
    return jsonify(ute.get_fraud_logs())

# ================= ADMIN ANALYTICS =================
@app.route("/api/admin/summary")
def admin_summary():
    return jsonify({
        "users": ute.get_total_users(),
        "system_balance": ute.get_total_system_balance(),
        "admin_earnings": ute.get_admin_earnings()
    })

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
