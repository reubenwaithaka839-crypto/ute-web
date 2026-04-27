import sqlite3

DB = "rw_prestige_final.db"

def calculate_prestige_split(gross, is_first=True):
    """
    Calculates the financial distribution based on employment status.
    First Month: 70% Net, 10% Rebate, 20% Treasury (+ 3% Fee included in Treasury calc per user logic)
    Subsequent: 90% Net, 2% Rebate, 8% Treasury (+ 3% Fee)
    """
    gross = float(gross)
    fee = gross * 0.03
    
    if is_first:
        # Protocol: Alpha
        emp_net = gross * 0.70
        rebate = gross * 0.10
        treasury = (gross * 0.20) + fee # Fee absorbed by treasury or added on top based on logic. Here added to Treasury bucket.
    else:
        # Protocol: Beta
        emp_net = gross * 0.90
        rebate = gross * 0.02
        treasury = (gross * 0.08) + fee
        
    return {
        "employee_net": round(emp_net, 2), 
        "employer_rebate": round(rebate, 2), 
        "treasury_total": round(treasury, 2),
        "fee_amount": round(fee, 2)
    }
