# ute.py - The Financial Logic Engine for UTE_WEB
DB = "rw_final_prestige.db"

def get_ute_math(amount):
    """
    Calculates platform deductions and net settlement amounts.
    10% goes to the platform, 90% to the user.
    """
    try:
        gross = float(amount)
        rate = 0.10 
        deduction = gross * rate
        net_to_bank = gross - deduction
        
        return {
            'gross': round(gross, 2),
            'deduction': round(deduction, 2),
            'net': round(net_to_bank, 2),
            'percent_rate': 10
        }
    except (ValueError, TypeError):
        return {'gross': 0.0, 'deduction': 0.0, 'net': 0.0, 'percent_rate': 0}
