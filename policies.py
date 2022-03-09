#!/usr/bin/env python
#
# policies.py
#

import numpy as np
from scipy.optimize import brentq
from functions import PLIF
from mortality import mortality_function_from_table

EPS = 1.0e-02
RMD_AGE = 70


def no_allocation_policy():
    """
    Make no attempt to rebalance the portfolio.
    """
    def _no_allocation_policy(ages,
                              assets_pretax,
                              assets_posttax,
                              assets_basis):
        tot_assets = sum(assets_pretax) + sum(assets_posttax)
        cashp = (assets_pretax[0] + assets_posttax[0])/tot_assets
        stockp = (assets_pretax[1] + assets_posttax[1])/tot_assets
        return [cashp, stockp]
    return _no_allocation_policy


def const_allocation_policy(ratios):
    """
    Return the constant allocation policy, where
    assets are allocated to cash and stocks in
    a fixed proportion.
    """
    def _const_allocation_policy(ages,
          assets_pretax,
          assets_posttax,
          assets_basis):
        return ratios
    return _const_allocation_policy


def age_based_alloc_policy():
    def _age_based_alloc_policy(ages,
          assets_pretax,
          assets_posttax,
          assets_basis):
        stockp = min(1.0, max(0.0, (140 - min(ages))/100.0))
        cashp = 1.0 - stockp
        return [cashp, stockp]
    return _age_based_alloc_policy


def const_spending_policy(amount):
    mortality = mortality_function_from_table('./552.csv')
    def _const_spending_policy(ages,
          ins_amts,
          assets_pretax,
          assets_posttax,
          assets_basis,
          ):
        # we only care about paying insurance premiums if there
        # are two surviving persons.
        if len(ages) > 1:
            ins_cost = ins_amts[0] * mortality(ages[0]) / 1.29
        else :
            ins_cost = 0
        totassets = sum(assets_pretax) + sum(assets_posttax)
        #
        # if there is only one person left, cost is 80% of two
        if len(ages) == 1:
            amount2 = 0.80 * amount
        else:
            amount2 = amount
        return min(totassets, amount2 + ins_cost)
    return _const_spending_policy


def basic_withdrawal_policy():
    """
    First take from post tax stuff, in proportion
    to what is there (keep cash/stock balance)

    Then take from pre tax stuff.
    """
    def _basic_withdrawal_policy(ages,
          assets_pretax,
          assets_posttax,
          assets_basis,
          total_tax_from_taxable_income,
          post_from_pre,
          pre_from_post,
          ule,  # for calculating required minimum distribution.
          spend):

        spend_orig = spend

        rmd_taxable_income = 0.0
        if ages[0] >= RMD_AGE:
            # we are subject to required minimum withdrawal
            expected_years_to_live = float(ule(ages[0]))
            a0 = assets_pretax[0]/expected_years_to_live
            a1 = assets_pretax[1]/expected_years_to_live
            assets_pretax[0] -= a0
            assets_pretax[1] -= a1
            assets_posttax[0] += a0
            assets_posttax[1] += a1
            assets_basis[0] += a0
            assets_basis[1] += a1
            rmd_taxable_income = a0 + a1

        post_tax_total = sum(assets_posttax)

        if spend < post_tax_total - total_tax_from_taxable_income(rmd_taxable_income+assets_posttax[0]-assets_basis[0] +
                                                                                     assets_posttax[1]-assets_basis[1]):
            # we can satisfy our spend from the post_tax pile
            p1 = assets_posttax[0] / post_tax_total
            p2 = assets_posttax[1] / post_tax_total
            p3 = assets_basis[0]/assets_posttax[0]
            p4 = assets_basis[1]/assets_posttax[1]

            def g(t):
                """
                t: total amount of money to withdraw from post tax pile
                """
                #
                # you only pay tax on the 'growth', not the basis
                #
                my_tax = total_tax_from_taxable_income(rmd_taxable_income+t*p1*(1-p3) + t*p2*(1-p4))
                return t * p1 + t * p2 - my_tax - spend
            withdrawal = brentq(g, 0, post_tax_total)
            if withdrawal < spend_orig:
                pass
            # return the amounts from pretax, post tax and new basis
            return (withdrawal,
                    [0, 0],
                    [withdrawal*p1, withdrawal*p2],
                    [assets_basis[0]-withdrawal*p1*p3, assets_basis[1]-withdrawal*p2*p4],
                    rmd_taxable_income)
        else:
            # you're spending all of your post-tax money, and now dipping into
            # pretax money.
            #
            # save tax1 for later
            #
            tax1 = total_tax_from_taxable_income(rmd_taxable_income+assets_posttax[0]-assets_basis[0] +
                                                 assets_posttax[1]-assets_basis[1])
            spend -= assets_posttax[0] + assets_posttax[1] - tax1

            pre_tax_total = sum(assets_pretax)
            tax2 = total_tax_from_taxable_income(rmd_taxable_income+assets_posttax[0]-assets_basis[0] +
                                                 assets_posttax[1]-assets_basis[1] + pre_tax_total)
            if spend < pre_tax_total - (tax2-tax1):
                # we can get what we want out of pretax
                def g(t):
                    """
                    t: total amount of money to withdraw
                    """
                    tax2 = total_tax_from_taxable_income(rmd_taxable_income+assets_posttax[0]-assets_basis[0] +
                                                         assets_posttax[1]-assets_basis[1]+t)
                    return t - (tax2-tax1) - spend
                w = brentq(g, 0, pre_tax_total)
                p1 = assets_pretax[0] / pre_tax_total
                p2 = assets_pretax[1] / pre_tax_total
                withdrawal = w + assets_posttax[0] + assets_posttax[1]
                if withdrawal < spend_orig:
                    pass
                return (withdrawal,
                        [w*p1, w*p2],
                        [assets_posttax[0], assets_posttax[1]],
                        [0, 0],
                        rmd_taxable_income)
            else:
                # you've spent it all
                withdrawal = sum(assets_pretax) + sum(assets_posttax)
                if withdrawal < spend_orig:
                    pass
                return (withdrawal,
                        [assets_pretax[0], assets_pretax[1]],
                        [assets_posttax[0], assets_posttax[1]],
                        [0, 0], rmd_taxable_income)
    return _basic_withdrawal_policy


def test():
    import tax
    import rmd

    # all money purely post tax
    #
    a_pre = [200_000, 1_800_000]
    a_post = [650_000,   350_000]
    a_basis = [650_000,   200_000]

    ages = [53, 53]

    def tot_tax(income):
        fed_tax = tax.tax_from_income(tax.fed_schedule2020mfj,
                                      tax.fed_std_deduction2020mfj,
                                      income)
        state_tax = tax.tax_from_income(tax.pa_schedule2020,
                                        0.0,
                                        income)
        return fed_tax + state_tax

    post_from_pre = tax.posttax_from_pretax(tax.fed_schedule2020mfj,
                                            tax.fed_std_deduction2020mfj,
                                                tax.pa_schedule2020,
                                                tax.pa_std_deduction2020)
    pre_from_post = post_from_pre.inverse()
    ule = rmd.uniform_life_expectancy('ult_2020.csv')

    annual_spend = 140000

    f = basic_withdrawal_policy()

    year = 2022
    tot_wealth = sum(a_pre) + sum(a_post)

    print(f'                     PreTaxC PreTaxStok PostTaxC PostTaxS   BasisC   BasisS ')
    print(f'                    {a_pre[0]:8,.0f} {a_pre[1]:10,.0f} {a_post[0]:8,.0f} {a_post[1]:8,.0f} {a_basis[0]:8,.0f} {a_basis[1]:8,.0f}')

    while ages[0] < 85 and tot_wealth > 0:
        withdrawal, pre, post, basis = f(ages,
                                         a_pre,
                                         a_post,
                                         a_basis,
                                         tot_tax,
                                         post_from_pre,
                                         pre_from_post,
                                         ule,
                                         annual_spend)
        a_pre[0] -= pre[0]
        a_pre[1] -= pre[1]
        a_post[0] -= post[0]
        a_post[1] -= post[1]
        a_basis[0] = basis[0]
        a_basis[1] = basis[1]
        tot_wealth = sum(a_pre) + sum(a_post)

        print(f'{year} {ages[0]} {ages[1]} {withdrawal:8,.0f} {a_pre[0]:8,.0f} {a_pre[1]:10,.0f} {a_post[0]:8,.0f} {a_post[1]:8,.0f} {a_basis[0]:8,.0f} {basis[1]:8,.0f}')
    
        year += 1
        ages[0] += 1
        ages[1] += 1
