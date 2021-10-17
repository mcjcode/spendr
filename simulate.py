#!/usr/bin/env python
#
# simulate.py
#

import numpy as np
import tax

tot_tax_mfj = tax.tot_tax(tax.fed_schedule2020mfj,
                          tax.fed_std_deduction2020mfj,
                          tax.pa_schedule2020,
                          tax.pa_std_deduction2020)

tot_tax_single = tax.tot_tax(tax.fed_schedule2020single,
                             tax.fed_std_deduction2020single,
                             tax.pa_schedule2020,
                             tax.pa_std_deduction2020)

def logmsg(str):
    print(str)

def path(ret_gen,
         allocation_policy,
         spending_policy,
         withdrawal_policy,
         mortality_tables,
         year,
         ages,
         assets_pretax,
         assets_posttax,
         assets_basis):

    ages = list(ages)
    assets_pretax = list(assets_pretax)
    assets_posttax = list(assets_posttax)
    assets_basis = list(assets_basis)
    
    alive = [True]*len(ages)
    tot_assets = sum(assets_pretax) + sum(assets_posttax)

    results = []
    while any(alive) and tot_assets > 0:
        #
        # find out how much money we intend to spend
        #
        spending_amt = spending_policy(ages,
                                       assets_pretax,
                                       assets_posttax,
                                       assets_basis)

    
        if sum(alive)==2:
            tot_tax_f = tot_tax_mfj
        else:
            tot_tax_f = tot_tax_single

        withdrawal, pre, post, basis = withdrawal_policy(ages,
                                                         assets_pretax,
                                                         assets_posttax,
                                                         assets_basis,
                                                         tot_tax_f,
                                                         spending_amt)
        ret = next(ret_gen)

        results.append([year, list(ages), list(alive), list(assets_pretax), list(assets_posttax), list(assets_basis), spending_amt, withdrawal, ret])

        assets_pretax[0] -= pre[0]
        assets_pretax[1] -= pre[1]
        assets_posttax[0] -= post[0]
        assets_posttax[1] -= post[1]
        assets_basis[0] = basis[0]
        assets_basis[1] = basis[1]

        tot_assets = sum(assets_pretax) + sum(assets_posttax)

        assets_pretax[1] *= np.exp(ret)
        assets_posttax[1] *= np.exp(ret)        
        
        for i in [0, 1]:
            # let's see if people survive to next year
            alive[i] = alive[i] and np.random.random() > mortality_tables[i](ages[i])/100.0
            # if they are alive, they get older
            if alive[i]:
                ages[i] += 1

        year += 1

    results.append([year, list(ages), list(alive), list(assets_pretax), list(assets_posttax), list(assets_basis), 0.0, 0.0, 0.0])
    return results

def test():
    import returns
    import policies
    import mortality

    ret_gen = returns.normal(0.06, 0.16)
    allocation_policy = policies.const_allocation_policy([0.30, 0.70])
    spending_policy = policies.const_spending_policy(140_000.0)
    withdrawal_policy = policies.basic_withdrawal_policy()
    mtable0 = mortality.mortality_function_from_table('552.csv')
    mtable1 = mortality.mortality_function_from_table('552.csv')
    mortality_tables = [mtable0, mtable1]
    year = 2020
    ages = [53, 53]
    assets_pretax = [ 200_000, 1_800_000]
    assets_posttax= [ 650_000,   350_000]
    assets_basis  = [ 650_000,   200_000]

    results = path(ret_gen,
         allocation_policy,
         spending_policy,
         withdrawal_policy,
         mortality_tables,
         year,
         ages,
         assets_pretax,
         assets_posttax,
         assets_basis)
    

    return results

def logrec(rec):
    year, [age0, age1], [alive0, alive1], [apret0, apret1], [apostt0, apostt1], [basis0, basis1], spend, withdrawal, rtrn = rec
    return f'{year} {age0} {age1} {str(alive0):5s} {str(alive1):5s} {apret0:10,.0f} {apret1:10,.0f} {apostt0:10,.0f}, {apostt1:10,.0f} {basis0:10,.0f} {basis1:10,.0f} {spend:8,.0f} {withdrawal:,.0f} {rtrn*100:5.1f}'
