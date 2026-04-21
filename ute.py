# ute.py - The Financial Logic Engine for UTE_WEB

def get_ute_math(amount):
    """
    Calculates platform deductions and net settlement amounts.
    This ensures the system always takes its cut before paying out.
    """
    try:
        # Convert to float to handle decimals
        gross = float(amount)
        
        # DEDUCTION LOGIC
        # Example: 10% Platform Fee (0.10)
        # You can change this 0.10 to 0.05 for 5%, etc.
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
        # Return zeros if the input is not a number
        return {'gross': 0, 'deduction': 0, 'net': 0, 'percent': 0}
