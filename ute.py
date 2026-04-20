def get_ute_math(salary, months_paid):
    """
    Calculates the 'Million Dollar' UTE Split.
    - Adds 3% service fee to the employer.
    - Keeps track of total months.
    """
    salary = float(salary)
    fee_percent = 0.03
    
    # Total the employer pays (Salary + 3%)
    total_to_pay = salary + (salary * fee_percent)
    
    # The net the employee receives 
    net_salary = salary 
    
    return {
        "total": round(total_to_pay, 2),
        "net": round(net_salary, 2),
        "fee": round(salary * fee_percent, 2)
    }
