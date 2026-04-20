import os
from flask import Flask, render_template, request, jsonify
from intasend import APIService

app = Flask(__name__)

# --- CONFIGURATION ---
# These pull from the Render Environment Variables you just set up
API_PUBLISHABLE_KEY = os.environ.get('INTASEND_PUBLISHABLE_KEY')
API_TOKEN = os.environ.get('INTASEND_API_TOKEN')

# Initialize IntaSend (Set test=True for your 10 KES testing)
service = APIService(token=API_TOKEN, publishable_key=API_PUBLISHABLE_KEY, test=True)

@app.route('/')
def index():
    """Landing Page / Login"""
    return render_template('auth.html')

@app.route('/dashboard')
def dashboard():
    """The High-End Dashboard"""
    # We are hardcoding 'admin' for now so you can see all your big buttons.
    # In a full app, this would come from a login check.
    user_context = {
        'role': 'admin', 
        'name': 'Developer'
    }
    return render_template('dashboard.html', user=user_context)

@app.route('/pay', methods=['POST'])
def initiate_payment():
    """Triggers the 10 KES STK Push to your phone"""
    try:
        response = service.collect.mpesa_stk_push(
            phone_number="2547XXXXXXXX", # Replace with your test phone number
            email="test@example.com",
            amount=10,
            narrative="Dashboard Service Payment"
        )
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/intasend-webhook', methods=['POST'])
def webhook():
    """The 'Handshake' that fixes the 'Processing' hang"""
    data = request.json
    state = data.get('invoice', {}).get('state')
    
    if state == 'COMPLETED':
        print("✅ PAYMENT SUCCESS: 10 KES Received!")
        # This is where your app officially records the payment as 'Done'
        return jsonify({"status": "success"}), 200
    
    return jsonify({"status": "received"}), 200

if __name__ == '__main__':
    # Required for Render to bind to the correct port
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
