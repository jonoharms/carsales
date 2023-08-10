import numpy_financial as npf
from decimal import Decimal, ROUND_HALF_DOWN


def D(num, prec='0.01'):
    return Decimal(num).quantize(Decimal(prec), rounding=ROUND_HALF_DOWN)

 

RESIDUAL = {
    1: D(0.6563, '0.0001'),
    2: D(0.55, '0.0001'),
    3: D(0.4688, '0.0001'),
    4: D(0.3750, '0.0001'),
    5: D(0.2813, '0.0001'),
}

 

TAX_RATE = D(0.325, '0.001')
MEDICARE_RATE = D(0.02, '0.01')

def calc_lease(financed_amount, residual, lease_term, interest_rate, months_deferred=None):

    monthly_interest_rate = float(interest_rate) / 12
    months = lease_term*12

    if months_deferred:
        interest = D(float(financed_amount)*monthly_interest_rate)
        financed_amount += interest
        months -= months_deferred

    monthly_lease = D(
        npf.pmt(
            monthly_interest_rate,
            months,
            -(float(financed_amount) - float(residual)),
        )
        + float(residual) * monthly_interest_rate
    )   # principal+interest on lease portion, interest only on residual

    fortnight_lease = D(monthly_lease * 12 / 26)
    total_cost = monthly_lease * months + residual

    print(f'financed_amount: ${financed_amount}')
    print(f'lease_term: {months} months')
    print(f'residual: ${residual}')
    print(f'monthly: ${monthly_lease}')
    print(f'fortnight: ${fortnight_lease}')
    print(f'total_cost: ${total_cost}\n')

 

financed_amount = D(80595)
lease_term = 2
interest_rate = D(0.0809, '0.0001')
residual = D(44000)
print('comm bank')
calc_lease(financed_amount, residual, lease_term, interest_rate, 2)

 
financed_amount = D(76500 + 400)
lease_term = 2
interest_rate = D(0.103, '0.0001')
residual = D(39746 * 1.1)
print('nla')
calc_lease(financed_amount, residual, lease_term, interest_rate, 2)

financed_amount = D(76507.28)
lease_term = 2
interest_rate = D(0.158, '0.0001')
residual = D(44303.03)
print('smartlease')
calc_lease(financed_amount, residual, lease_term, interest_rate, 2)

 