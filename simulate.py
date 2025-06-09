#!/usr/bin/env python
#
# simulate.py
#

import numpy as np
import pandas as pd
import tax
import ssn


def print_withdrawal_info(a, w, pr, po, bs):
    print(f'{a[0]:3d} {a[1]:3d} {w:10.2f} {pr[0]:10.2f} {pr[1]:10.2f} {po[0]:10.2f} {po[1]:10.2f} {bs[0]:10.2f} {bs[1]:10.2f}')


post_from_pre_mfj = tax.posttax_from_pretax(tax.fed_schedule2020mfj,
                                            tax.fed_std_deduction2020mfj,
                                            tax.pa_schedule2020,
                                            tax.pa_std_deduction2020)
pre_from_post_mfj = post_from_pre_mfj.inverse()

post_from_pre_single = tax.posttax_from_pretax(tax.fed_schedule2020single,
                                               tax.fed_std_deduction2020single,
                                               tax.pa_schedule2020,
                                               tax.pa_std_deduction2020)
pre_from_post_single = post_from_pre_single.inverse()


def tot_tax_mfj(income):
    return income - post_from_pre_mfj(income)


def tot_tax_single(income):
    return income - post_from_pre_single(income)


def logmsg(s: str):
    print(s)


def path(ret_gen,
         allocation_policy,
         spending_policy,
         withdrawal_policy,
         mortality_tables,
         year,
         ages,
         assets_pretax,
         assets_posttax,
         assets_basis,
         ule,
         retirement_age,
         insurance_amts0):
    ages = list(ages)
    assets_pretax = list(assets_pretax)
    assets_posttax = list(assets_posttax)
    assets_basis = list(assets_basis)

    alive = [True] * len(ages)
    tot_assets = sum(assets_pretax) + sum(assets_posttax)
    ssn_income = ssn.ssn_if_retired_at(retirement_age)

    results = []

    my_ssn = 0.0
    carry_forward_loss = 0
    #
    # keep going until they are all dead or run out of money
    #
    insurance_amts = list(insurance_amts0)

    while any(alive) and tot_assets > 0:
        surviving_ages = [age for (age, a) in zip(ages, alive) if a]
        surviving_insurance_amts = [amt for (amt, a) in zip(insurance_amts, alive)]
        #
        # find out how much money we intend to spend
        #
        spending_amt = spending_policy(surviving_ages,
                                       surviving_insurance_amts,
                                       assets_pretax,
                                       assets_posttax,
                                       assets_basis)

        
        if max(ages[0], ages[1]) >= retirement_age:
            my_ssn = ssn_income

        if sum(alive) == 2:
            tot_tax_f = tot_tax_mfj
            post_from_pre = post_from_pre_mfj
            pre_from_post = pre_from_post_mfj
        else:
            tot_tax_f = tot_tax_single
            post_from_pre = post_from_pre_single
            pre_from_post = pre_from_post_single

        # now figure out how much we need to withdraw in
        # order to meet our spending goal.
        #
        args = [surviving_ages,
                assets_pretax,
                assets_posttax,
                assets_basis,
                tot_tax_f,
                post_from_pre,
                pre_from_post,
                ule,
                spending_amt]
        withdrawal, pre, post, basis, rmd_taxable_income = withdrawal_policy(*args)

        # compute how much taxable income we are generating
        #
        taxable_income = sum(pre)
        taxable_income += (post[0] - (assets_basis[0] - basis[0]))
        taxable_income += (post[1] - (assets_basis[1] - basis[1]))
        taxable_income += rmd_taxable_income

        if not alive[0]:
            ins_payout = insurance_amts[0]
            insurance_amts[0] = 0
        else:
            ins_payout = 0

        if taxable_income < 0:
            carry_forward_loss += taxable_income
            taxable_income = 0
        else:
            applied_carry_forward = min(taxable_income, -carry_forward_loss)
            taxable_income -= applied_carry_forward
            carry_forward_loss += applied_carry_forward

        ret = next(ret_gen)
        
        results.append([year] + ages + alive + assets_pretax + assets_posttax + assets_basis +
                       [spending_amt, withdrawal, taxable_income, ret, my_ssn, ins_payout, rmd_taxable_income, carry_forward_loss])

        assets_pretax[0] -= pre[0]
        assets_pretax[1] -= pre[1]
        assets_posttax[0] -= post[0]
        assets_posttax[1] -= post[1]
        assets_basis[0] = basis[0]
        assets_basis[1] = basis[1]

        tot_assets = sum(assets_pretax) + sum(assets_posttax)
        #
        # are we out of money? If so, game over
        if tot_assets <= 0.0:
            break

        # Account for investment growth and income
        #
        growth_factor = np.exp(ret)
        assets_pretax[1] *= growth_factor
        assets_posttax[1] *= growth_factor
        
        #
        # add the ss and insurance money to posttax
        # in the same proportion as they are currently
        # allocated
        #
        
        tot = float(sum(assets_pretax) + sum(assets_posttax))
        if tot > 0:
            cash_ratio = (assets_posttax[0]+assets_pretax[0])/tot
        else:
            cash_ratio = 0.25
        cash_piece = (my_ssn + ins_payout) * cash_ratio
        stock_piece = (my_ssn + ins_payout) - cash_piece
        assets_posttax[0] += cash_piece
        assets_posttax[1] += stock_piece
        assets_basis[0] += cash_piece
        assets_basis[1] += stock_piece
        
        #
        # now rebalance the portfolio
        #
        cashp, _ = allocation_policy(surviving_ages,
                                     assets_pretax,
                                     assets_posttax,
                                     assets_basis)
        totpretax = sum(assets_pretax)
        tot = float(sum(assets_pretax) + sum(assets_posttax))
        proposed_pretax_cash = float(cashp * tot - assets_posttax[0])
        assets_pretax[0] = min(max([proposed_pretax_cash, 0.0]), totpretax)
        assets_pretax[1] = totpretax - assets_pretax[0]

        # let's see if people survive to next year
        for i in [0, 1]:
            alive[i] = alive[i] and np.random.random() > mortality_tables[i](ages[i])
            # if they are alive, they get older
            if alive[i]:
                ages[i] += 1

        year += 1

    assets_pretax = [np.floor(xx) for xx in assets_pretax]
    assets_posttax = [np.floor(xx) for xx in assets_posttax]
    assets_basis = [np.floor(xx) for xx in assets_posttax]

    results.append([year] + ages + alive + assets_pretax + assets_posttax + assets_basis + [0.0]*8)

    return results


def test_yaml(config_fn):
    import returns
    import policies
    import mortality
    import rmd
    import yaml

    with open(config_fn, 'r') as stream:
        dictionaries = yaml.load_all(stream, yaml.Loader)
        params = next(dictionaries)

    for key, value in params.items():
        print(key + " : " + str(value))

    nsims = params['nsims']
    retirement_age = params['retirement_age']
    year = params['year']
    ages = params['ages']
    genders = params['genders']
    assets_pretax = params['assets_pretax']
    assets_posttax = params['assets_posttax']
    assets_basis = params['assets_basis']
    ret_gen = eval(params['ret_gen'])
    allocation_policy = eval(params['allocation_policy'])
    spending_policy = eval(params['spending_policy'])
    withdrawal_policy = eval(params['withdrawal_policy'])
    insurance_amts = params['insurance_amts']

    seed = params['seed']
    
    np.random.seed(seed)
    
    ule = rmd.uniform_life_expectancy('ult_2020.csv')
    mtable = {'M': '552.csv', 'F': '553.csv'}
    mortality_tables = [mortality.mortality_function_from_table(mtable[gender]) for gender in genders]

    sims = []
    for ii in range(nsims):
        results = path(ret_gen,
                       allocation_policy,
                       spending_policy,
                       withdrawal_policy,
                       mortality_tables,
                       year,
                       ages,
                       assets_pretax,
                       assets_posttax,
                       assets_basis,
                       ule,
                       retirement_age,
                       insurance_amts)
        sims += [[ii + 1] + rec for rec in results]

    colnames = 'Sim Year A1 A2 Surv1 Surv2 Cash401k Stock401k PstTaxCash PstTaxStok CashBasis StockBasis Spend Withdraw Taxable Return SSN Ins RMD CarryFwd'.split()
    data = {k: v for (k, v) in zip(colnames, list(zip(*sims)))}
    df = pd.DataFrame(data)
    df['TotAssets'] = df.Cash401k + df.Stock401k + df.PstTaxCash + df.PstTaxStok
    df['Last'] = (df.TotAssets == 0) | (~(df.Surv1 | df.Surv2))
    df['CashAlloc'] = (df.Cash401k + df.PstTaxCash) / df.TotAssets
    df.Return = 100 * df.Return
    df['Taxes'] = df.Withdraw - df.Spend

    return df


def test():
    import returns
    import policies
    import mortality
    import ssn
    import rmd

    retirement_age = 70
    ule = rmd.uniform_life_expectancy('ult_2020.csv')
    ret_gen = returns.normal(0.07, 0.16)
    allocation_policy = policies.age_based_alloc_policy()  # policies.const_allocation_policy(alloc)
    spending_policy = policies.const_spending_policy(150_000.0)
    withdrawal_policy = policies.basic_withdrawal_policy()
    mtable0 = mortality.mortality_function_from_table('552.csv')
    mtable1 = mortality.mortality_function_from_table('553.csv')
    mortality_tables = [mtable0, mtable1]
    year = 2022
    ages = [54, 54]
    assets_pretax = [207_000, 2_030_000]
    assets_posttax = [790_000, 1_000_000]  # 566_000] #566_000
    assets_basis = [700_000, 600_000]  # note that cash basis < cash.  # 200_000]

    results = path(ret_gen,
                   allocation_policy,
                   spending_policy,
                   withdrawal_policy,
                   mortality_tables,
                   year,
                   ages,
                   assets_pretax,
                   assets_posttax,
                   assets_basis,
                   ule,
                   retirement_age)

    return results


def log_record(rec):
    year, age0, age1, alive0, alive1, apret0, apret1, apostt0, apostt1, basis0, basis1, spend, withdrawal, taxable, rtrn, my_ssn = rec
    return f'{year} {age0} {age1} {str(alive0):5s} {str(alive1):5s} {apret0:10,.0f} {apret1:10,.0f} {apostt0:10,.0f} {apostt1:10,.0f} {basis0:10,.0f} {basis1:10,.0f} {spend:8,.0f} {withdrawal:8,.0f} {taxable:8,.0f} {my_ssn:8,.0f} {rtrn * 100:6.1f}'


def print_test_sim():
    recs = test()
    print(
        'Year A1 A2 Surv1 Surv2 PreTaxCash PreTaxStok PstTaxCash PstTaxStok PstTxBasis PstTxBasis    Spend Withdraw Taxable      SSN Return')
    for rec in recs:
        print(log_record(rec))


def do_test_sims(nsim):
    sims = [[ii + 1] + rec for ii in range(nsim) for rec in test()]
    return sims
