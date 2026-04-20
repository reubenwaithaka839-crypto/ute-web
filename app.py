import os
from flask import Flask, render_template, request, jsonify
from intasend import APIService

app = Flask(__name__)

# These pull from your Render "Environment Variables"
API_PUBLISHABLE_KEY = os.environ.get('INTASEND_PUBLISHABLE_KEY', '').strip()
API_TOKEN = os.environ.get('INTASEND_API_TOKEN', '').strip()

# Initialize IntaSend (test=True is for Sandbox testing)
service = APIService(token=API_TOKEN, publishable_key=API_PUBLISHABLE_KEY, test=True)

@app.route('/')
def index():
    # Hardcoded 'admin' role so you see all the premium buttons immediately
    user_data = {'role': 'admin', 'name': 'Developer'}
    return render_template('dashboard.html', user=user_data)

@app.route('/pay', methods=['POST'])
def initiate_payment():
    try:
        # Using your provided test number
        response = service.collect.mpesa_stk_push(
            phone_number="254750289733", 
            email="test@example.com",
            amount=10,
            narrative="Premium Upgrade Test"
        )
        return jsonify(response)
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/intasend-webhook', methods=['POST'])
def webhook():
    return jsonify({"status": "received"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
