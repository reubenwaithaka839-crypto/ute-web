# ute.py - The Financial Logic Engine for UTE_WEB

def get_ute_math(amount):
    """
    Calculates platform deductions and net settlement amounts.
    """
    try:
        gross = float(amount)
        # 10% Platform Fee
        rate = 0.10 
        deduction = gross * rate
        net_to_bank = gross - deduction
        
        return {
            'gross': round(gross, 2),
            'deduction': round(deduction, 2),
            'net': round(net_to_bank, 2),
            'percent': int(rate * 100)
        }
    except (ValueError, TypeError):
        return {'gross': 0, 'deduction': 0, 'net': 0, 'percent': 0}
