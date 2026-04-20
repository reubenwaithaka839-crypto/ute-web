import os
from flask import Flask, render_template, request, jsonify
from intasend import APIService

app = Flask(__name__)

# --- CONFIGURATION ---
# IMPORTANT: These MUST match your Render Environment Keys exactly
API_PUBLISHABLE_KEY = os.environ.get('INTASEND_PUBLISHABLE_KEY')
API_TOKEN = os.environ.get('INTASEND_API_TOKEN')

# Initialize Service
service = APIService(token=API_TOKEN, publishable_key=API_PUBLISHABLE_KEY, test=True)

@app.route('/')
def index():
    user_data = {'role': 'admin', 'name': 'Developer'}
    return render_template('dashboard.html', user=user_data)

@app.route('/pay', methods=['POST'])
def initiate_payment():
    try:
        # LOGGING: This will show up in your Render Logs tab
        print(f"--- Attempting Payment with Key: {API_PUBLISHABLE_KEY[:10]}... ---")
        
        response = service.collect.mpesa_stk_push(
            phone_number="254722000000", # <--- CHANGE THIS TO YOUR REAL NUMBER
            email="test@example.com",
            amount=10,
            narrative="Dashboard Service"
        )
        print(f"IntaSend Response: {response}")
        return jsonify(response)
    except Exception as e:
        # This will tell us the EXACT error (e.g., 'Unauthorized' or 'Invalid Number')
        print(f"!!! CRITICAL ERROR: {str(e)}") 
        return jsonify({"error": str(e)}), 400

@app.route('/intasend-webhook', methods=['POST'])
def webhook():
    data = request.json
    print(f"Webhook Received: {data}")
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
