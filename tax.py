#!/usr/bin/env python
#
# tax.py
#
from functions import PLIF
from scipy.optimize import bisect

#
# for some solvers below, we assume that the total tax rate
# is never larger than this level
#
MAXTAX = 0.75
INF = float('inf')

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

# in what year do we turn 72?  2040
#

fed_schedule2020mfj = [
    (19750.0, 0.10),  # 10% tax on income up to 19,750.00
    (80250.0, 0.12),
    (171050.0, 0.22),
    (326600.0, 0.24),
    (414700.0, 0.32),
    (622050.0, 0.35),
    (INF, 0.37)]  # 37% tax on income higher than 622,050
fed_std_deduction2020mfj = 24800.0

fed_schedule2020single = [
    (9875.0, 0.10),
    (40125.0, 0.12),
    (85525.0, 0.22),
    (163300.0, 0.24),
    (207350.0, 0.32),
    (518400.0, 0.35),
    (INF, 0.37)]
fed_std_deduction2020single = 12400.0

pa_schedule2020 = [
    (INF, 0.0307)]
pa_std_deduction2020 = 0.0


def posttax_from_pretax(fed_schedule,
                        fed_std_deduction,
                        state_schedule,
                        state_std_deduction):
    """
    :param fed_schedule: the federal schedule of marginal income tax rates
    :param fed_std_deduction: the federal standard deduction
    :param state_schedule: the state schedule of marginal income tax rates
    :param state_std_deduction: the state standard deduction
    :return: a PLIF which computes post-tax dollars from pretax dollar
    """
    xs = [fed_std_deduction] + [fed_std_deduction + z for (z, _) in fed_schedule[:-1]]
    xs += [state_std_deduction] + [state_std_deduction + z for (z, _) in state_schedule[:-1]]
    xs = sorted(xs)
    xs.append(xs[-1]+1.0)
    ttf = tot_tax(fed_schedule, fed_std_deduction, state_schedule, state_std_deduction)
    ys = [x-ttf(x) for x in xs]
    return PLIF(xs, ys)


def tax_from_income(schedule, std_deduction, income):
    ti = max(0, income - std_deduction)
    tax = 0.0
    prev_threshold = 0.0
    for (threshold, rate) in schedule:
        amt = min(threshold, ti)
        tax += (amt - prev_threshold) * rate
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

    def f1(income):
        return tax_from_income(fed_schedule,
                               fed_std_deduction,
                               income)

    def f2(income):
        return tax_from_income(state_schedule,
                               state_std_deduction,
                               income)

    def f(income):
        return income - (f1(income) + f2(income)) - spend

    return bisect(f, 0.0, (1 / MAXTAX) * spend)


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
