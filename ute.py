# ute.py - The Financial Logic Engine (v4.0 Platinum)
DB = "rw_prestige_v4.db"

def get_ute_math(amount):
    try:
        gross = float(amount)
        # Platform takes 10% standard, 30% on first placement
        platform_cut = gross * 0.10
        placement_bonus = gross * 0.30
        
        return {
            'gross': round(gross, 2),
            'net_to_talent': round(gross - platform_cut, 2),
            'platform_revenue': round(platform_cut, 2),
            'placement_revenue': round(placement_bonus, 2)
        }
    except:
        return {'gross': 0, 'net_to_talent': 0, 'platform_revenue': 0}
