# ute.py - The Financial Logic Engine for UTE_WEB

def get_ute_math(amount):
    """
    Calculates platform deductions and net settlement amounts.
    This ensures the system always takes its cut (10%) before 
    the money is queued for bank transfer.
    """
    try:
        # Convert input to float to handle decimals safely
        gross = float(amount)
        
        # --- UTE DEDUCTION LOGIC ---
        # Current Rate: 10% (0.10)
        rate = 0.10 
        
        # Calculate the "Cut" the platform keeps
        deduction = gross * rate
        
        # Calculate the actual money to be sent to the bank
        net_to_bank = gross - deduction
        
        # Return a dictionary of results for the app to use
        return {
            'gross': round(gross, 2),
            'deduction': round(deduction, 2),
            'net': round(net_to_bank, 2),
            'percent_rate': int(rate * 100)
        }
        
    except (ValueError, TypeError):
        # Fallback if the amount provided isn't a valid number
        return {
            'gross': 0.0,
            'deduction': 0.0,
            'net': 0.0,
            'percent_rate': 0
        }
