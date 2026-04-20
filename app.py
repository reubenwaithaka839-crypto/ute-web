import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from intasend import APIService

app = Flask(__name__)

# --- CONFIGURATION (Pulls from Render Environment Variables) ---
# Use your IntaSend Publishable Key and API Token here
API_PUBLISHABLE_KEY = os.environ.get('INTASEND_PUBLISHABLE_KEY')
API_TOKEN = os.environ.get('INTASEND_API_TOKEN')
# We use 'test=True' for your 10 KES testing. Change to False for Live.
service = APIService(token=API_TOKEN, publishable_key=API_PUBLISHABLE_KEY, test=True)

# --- ROUTES ---

@app.route('/')
def index():
    # This is your landing page with the "Million-Dollar" buttons
    # We pass a 'user_role' to test the Admin vs Employee view
    return render_template('index.html', user_role='admin')

@app.route('/pay', methods=['POST'])
def initiate_payment():
    """Triggers the 10 KES M-Pesa STK Push"""
    try:
        # Collecting 10 KES
        response = service.collect.mpesa_stk_push(
            phone_number="2547XXXXXXXX", # The phone number to prompt
            email="user@example.com",
            amount=10,
            narrative="Purchase Test"
        )
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/intasend-webhook', methods=['POST'])
def webhook():
    """This is the 'Handshake' URL IntaSend calls when payment is done"""
    data = request.json
    state = data.get('invoice', {}).get('state')
    invoice_id = data.get('invoice', {}).get('invoice_id')

    if state == 'COMPLETED':
        print(f"✅ Payment Success for Invoice {invoice_id}!")
        # Logic to update your database or unlock features goes here
        return jsonify({"status": "success"}), 200
    
    elif state == 'FAILED':
        print(f"❌ Payment Failed for Invoice {invoice_id}.")
        return jsonify({"status": "failed"}), 200

    return jsonify({"status": "processing"}), 200

@app.route('/dashboard')
def dashboard():
    """The high-end dashboard interface"""
    # Logic to ensure the 'Admin' option shows correctly
    user_role = 'admin' # This would normally come from your login session
    return render_template('dashboard.html', role=user_role)

if __name__ == '__main__':
    # Render uses the 'PORT' environment variable automatically
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
