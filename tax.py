#!/usr/bin/env python
#
# tax.py
#

from scipy.optimize import bisect

#
# for some solvers below, we assume that the total tax rate
# is never larger than this level
#
MAXTAX = 0.75 
INF = float('inf')

fed_schedule2020single = [(   9875.0, 0.10),
                          (  40125.0, 0.12),
                          (  85525.0, 0.22),
                          ( 163300.0, 0.24),
                          ( 207350.0, 0.32),
                          ( 518401.0, 0.35),
                          (      INF, 0.37)]

fed_std_deduction_single = 12400.00

#
#
# 0.10 * (19750.0) +
# 0.12 * (80250.0-19750.0) +
# 0.22 * (140000.0-24800.0-80250.0) =
# 16924.0
#
# a 140,000 dollar withdrawal would incur
# 16,924 in federal tax.  This would be a rate of
# approximately 12%
#

#
# in what year do we turn 72?  2040
#
# 
#


fed_schedule2020mfj    = [(  19750.0, 0.10),
                          (  80250.0, 0.12),
                          ( 171050.0, 0.22),
                          ( 326600.0, 0.24),
                          ( 414700.0, 0.32),
                          ( 622050.0, 0.35),
                          (      INF, 0.37)]

fed_schedule2020single = [(   9875.0, 0.10),
                          (  40125.0, 0.12),
                          (  85525.0, 0.22),
                          ( 163300.0, 0.24),
                          ( 207350.0, 0.32),
                          ( 518400.0, 0.35),
                          (      INF, 0.37)]

fed_std_deduction2020mfj  = 24800.0

fed_std_deduction2020single = 12400.0

pa_schedule2020        = [(      INF, 0.0307)]
pa_std_deduction2020   = 0.0

def tax_from_income(schedule, std_deduction, income):
    ti = max(0,income - std_deduction)
    tax = 0.0
    prev_threshold = 0.0
    for (threshold, rate) in schedule:
        amt = min(threshold, ti)
        tax += (amt - prev_threshold)*rate
        if threshold > ti:
            break
        prev_threshold = threshold
    return tax

def pretax_income_from_desired_spend(fed_schedule,
                                     fed_std_deduction,
                                     state_schedule,
                                     state_std_deduction,
                                     spend):
    """
    We want to know how much pre-tax money we need
    to achieve a post-tax level of income.
    """

    f1 = lambda income : tax_from_income(fed_schedule,
                                         fed_std_deduction,
                                         income)
    f2 = lambda income : tax_from_income(state_schedule,
                                         state_std_deduction,
                                         income)
    f = lambda income : income - (f1(income) + f2(income)) - spend

    retval = bisect(f, 0.0, (1/MAXTAX)*spend)

    return retval
    
def tot_tax(fed_schedule,
            fed_std_deduction,
            state_schedule,
            state_std_deduction):
    def f(income):
        fed_tax = tax_from_income(fed_schedule,
                                  fed_std_deduction,
                                  income)
        state_tax = tax_from_income(state_schedule,
                                    state_std_deduction,
                                    income)
        return fed_tax + state_tax
    return f
