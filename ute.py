# ute.py - The Financial Logic Engine (v3.1)
DB = "rw_prestige_v3.db"

def get_ute_math(amount):
    """
    Investor Logic: Calculates Platform Take-Rate
    Standard Platform Fee: 10%
    First Placement Fee (One-off): 30%
    """
    try:
        gross = float(amount)
        # Platform Revenue
        std_fee = gross * 0.10
        placement_fee = gross * 0.30

        return {
            'gross': round(gross, 2),
            'talent_net': round(gross - std_fee, 2),
            'platform_profit': round(std_fee, 2),
            'investor_yield': round(placement_fee, 2)
        }
    except Exception:
        return {'gross': 0.0, 'talent_net': 0.0, 'platform_profit': 0.0}
