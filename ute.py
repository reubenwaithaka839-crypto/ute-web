"""
UTE CORE CONTROLLER
This file initializes and links:
- app.py (main backend)
- mpesa.py (payment engine)
"""

from app import app, init_db
from mpesa import Mpesa
import os

# ================= INITIALIZE SYSTEM =================
print("Starting UTE Fintech System...")

# Ensure database is created
init_db()

# ================= M-PESA CONFIG CHECK =================
required_env = [
    "MPESA_KEY",
    "MPESA_SECRET",
    "MPESA_SHORTCODE",
    "MPESA_PASSKEY"
]

missing = [key for key in required_env if not os.environ.get(key)]

if missing:
    print("WARNING: Missing environment variables:")
    for m in missing:
        print(f"- {m}")
else:
    print("M-Pesa environment variables loaded successfully")

# ================= START APP =================
if __name__ == "__main__":
    print("UTE System Running...")
    app.run(host="0.0.0.0", port=5000, debug=True)
