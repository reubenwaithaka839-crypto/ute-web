import sqlite3

DB = "rw_prestige_final.db"

def calculate_prestige_split(gross, is_first=True):
    gross = float(gross)
    fee = gross * 0.03
    if is_first:
        emp_net, rebate, treasury = gross * 0.70, gross * 0.10, (gross * 0.20) + fee
    else:
        emp_net, rebate, treasury = gross * 0.90, gross * 0.02, (gross * 0.08) + fee
    return {"employee_net": round(emp_net, 2), "employer_rebate": round(rebate, 2), "treasury_total": round(treasury, 2)}
