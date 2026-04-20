import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# This pulls the token you just pasted into Render!
INTASEND_SECRET_TOKEN = os.environ.get('NGROK_AUTHTOKEN') 

@app.route('/intasend-webhook', methods=['POST'])
def handle_webhook():
    data = request.json
    # Check if the payment is actually completed
    state = data.get('invoice', {}).get('state')
    
    if state == 'COMPLETED':
        print("Success! The 10 KES was paid.")
        # Here is where you'd update your database or your big dashboard buttons
        return jsonify({"status": "success"}), 200
    
    return jsonify({"status": "ignored"}), 200
