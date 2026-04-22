# ute.py - The Financial Logic Engine
DB = "rw_prestige_v3.db" 

def get_ute_math(amount):
    """
    Calculates platform deductions.
    Standard: 10%
    First Placement: 30%
    """
    try:
        gross = float(amount)
        # Standard rate
        std_deduction = gross * 0.10
        # First month rate
        placement_deduction = gross * 0.30
        
        return {
            'gross': round(gross, 2),
            'std_net': round(gross - std_deduction, 2),
            'placement_net': round(gross - placement_deduction, 2),
            'std_fee': round(std_deduction, 2),
            'placement_fee': round(placement_deduction, 2)
        }
    except:
        return {'gross': 0.0, 'std_fee': 0.0, 'placement_fee': 0.0}
