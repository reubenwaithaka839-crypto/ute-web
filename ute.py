DB = "rw_prestige_pro.db"

def get_ute_math(salary, months_paid=0):
    gross = float(salary)
    # Business logic: 30% first month, 10% thereafter
    if months_paid == 0: 
        platform_fee = gross * 0.30
        employer_net = gross * 0.50
        employee_net = gross * 0.20
    else:
        platform_fee = gross * 0.10
        employer_net = gross * 0.60
        employee_net = gross * 0.30
        
    return {
        'gross': round(gross, 2),
        'platform_fee': round(platform_fee, 2),
        'employer_net': round(employer_net, 2),
        'employee_net': round(employee_net, 2)
    }
