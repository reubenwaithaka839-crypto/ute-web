import os
from flask import Flask, render_template, request, jsonify
from intasend import APIService

app = Flask(__name__)

# --- CONFIGURATION ---
API_PUBLISHABLE_KEY = os.environ.get('INTASEND_PUBLISHABLE_KEY')
API_TOKEN = os.environ.get('INTASEND_API_TOKEN')

# Initialize IntaSend Service
# Set test=True for Sandbox, test=False for Live
service = APIService(token=API_TOKEN, publishable_key=API_PUBLISHABLE_KEY, test=True)

@app.route('/')
def index():
    """Main Dashboard View"""
    # Dynamic Role Logic: Change 'admin' to 'employee' to see the difference
    user_data = {
        'role': 'admin', 
        'name': 'Developer'
    }
    return render_template('dashboard.html', user=user_data)

@app.route('/pay', methods=['POST'])
def initiate_payment():
    """Initiates the 10 KES STK Push"""
    try:
        # IMPORTANT: Use a real phone number in 254... format here
        response = service.collect.mpesa_stk_push(
            phone_number="254700000000", 
            email="user@example.com",
            amount=10,
            narrative="Dashboard Service Upgrade"
        )
        return jsonify(response)
    except Exception as e:
        print(f"Payment Error: {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/intasend-webhook', methods=['POST'])
def webhook():
    """Handles the payment confirmation from IntaSend"""
    data = request.json
    state = data.get('invoice', {}).get('state')
    
    if state == 'COMPLETED':
        print("✅ SUCCESS: Payment verified via Webhook!")
        return jsonify({"status": "success"}), 200
    
    return jsonify({"status": "processing"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
