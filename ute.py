import sqlite3

DB = "rw_prestige_final.db"

def calculate_prestige_split(gross, is_first=True):
    gross = float(gross)
    fee = gross * 0.03
    
    if is_first:
        emp_net = gross * 0.70
        rebate = gross * 0.10
        treasury = (gross * 0.20) + fee 
    else:
        emp_net = gross * 0.90
        rebate = gross * 0.02
        treasury = (gross * 0.08) + fee
        
    return {
        "employee_net": round(emp_net, 2), 
        "employer_rebate": round(rebate, 2), 
        "treasury_total": round(treasury, 2),
        "fee_amount": round(fee, 2)
    }
