#!/usr/bin/env python
#
# policies.py
#

from scipy.optimize import bisect

def const_allocation_policy(ratios):
    """
    Return the constant allocation policy, where
    assets are allocated to cash and stocks in
    a fixed proportion.
    """
    def f(ages,
          assets_pretax,
          assets_posttax,
          assets_basis):
        return ratios, ratios
    return f

def const_spending_policy(amount):
    def f(ages,
          assets_pretax,
          assets_posttax,
          assets_basis):

        totassets = sum(assets_pretax) + sum(assets_posttax)
        return min(totassets,amount)

    return f

def basic_withdrawal_policy():
    """
    First take from post tax stuff, in proportion
    to what is there (keep cash/stock balance)

    Then take from pre tax stuff.
    """
    def f(ages,
          assets_pretax,
          assets_posttax,
          assets_basis,
          total_tax_from_taxable_income,
          spend):

        post_tax_total = sum(assets_posttax)

        if spend < post_tax_total - total_tax_from_taxable_income(assets_posttax[1]-assets_basis[1]):
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
                mytax = total_tax_from_taxable_income(t*p2*(1-p4))
                ##print(p1,p2,mytax)
                return t * p1 + t * p2 - mytax - spend
            retval = bisect(g, 0, post_tax_total)
            # return the amounts from pretax, post tax and new basis
            return retval, [0, 0], [retval*p1, retval*p2], [assets_basis[0]-retval*p1*p3, assets_basis[1]-retval*p2*p4]
        else:
            # you're spending all of your post-tax money, and now dipping into
            # pretax money.
            #
            # save tax1 for later
            #
            tax1 = total_tax_from_taxable_income(assets_posttax[1])
            spend -= assets_posttax[0] + (assets_posttax[1] - tax1)

            pre_tax_total = sum(assets_pretax)
            tax2 = total_tax_from_taxable_income(assets_posttax[1]-assets_basis[1]+pre_tax_total)
            if spend < pre_tax_total - (tax2-tax1):
                p1 = assets_pretax[0] / pre_tax_total
                p2 = assets_pretax[1] / pre_tax_total
                # we can get what we want out of pretax
                def g(t):
                    """
                    t: total amount of money to withdraw
                    """
                    tax2 = total_tax_from_taxable_income(assets_posttax[1]-assets_basis[1]+t)
                    return t - (tax2-tax1) - spend
                w = bisect(g, 0, pre_tax_total)
                return w, [w*p1, w*p2], [assets_posttax[0],assets_posttax[1]], [0,0]
            else:
                # you've spent it all
                withdrawal = sum(assets_pretax) + sum(assets_posttax)
                return (withdrawal,
                        [assets_pretax[0],assets_pretax[1]],
                        [assets_posttax[0],assets_posttax[1]],
                        [0,0])
    return f

def test():
    import tax

    # all money purely post tax
    #
    a_pre   = [ 200_000, 1_800_000]
    a_post  = [ 650_000,   350_000]
    a_basis = [ 650_000,   200_000]

    ages   = [53, 53]

    def tot_tax(income):
        fed_tax = tax.tax_from_income(tax.fed_schedule2020mfj,
                                      tax.fed_std_deduction2020mfj,
                                      income)
        state_tax = tax.tax_from_income(tax.pa_schedule2020,
                                        0.0,
                                        income)
        return fed_tax + state_tax

    annual_spend = 140000

    f = basic_withdrawal_policy()

    year = 2022
    tot_wealth = sum(a_pre) + sum(a_post)

    print(f'                    {a_pre[0]:8,.0f} {a_pre[1]:10,.0f} {a_post[0]:8,.0f} {a_post[1]:8,.0f} {a_basis[0]:8,.0f} {a_basis[1]:8,.0f}')

    while ages[0] < 85 and tot_wealth > 0:
        withdrawal, pre, post, basis = f(ages,
                                         a_pre,
                                         a_post,
                                         a_basis,
                                         tot_tax,
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
