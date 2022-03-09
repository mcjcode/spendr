#!/usr/bin/env python
#
# ssn.py
#

import math

def index_factors(fn):

    h = {}
    max_year = 0
    with open(fn,'r') as fp:
        for line in fp:
            if not line.startswith('#'):
                rec = line.split(',')
                year = int(rec[0])
                max_earn = float(rec[1])
                index_factor = float(rec[2])
                h[year] = (max_earn, index_factor)
                max_year = max(max_year, year)
    
    def f(year):
        if year > max_year:
            year = max_year
        return h[year]

    return f

def calc_full_benefit(annual_earnings, index_factors):

    indexed_earnings = []
    print(annual_earnings)
    for (year, earnings) in annual_earnings:
        max_earn, index_factor = index_factors(year)
        indexed_earn = min(max_earn, earnings) * index_factor
        indexed_earnings.append(indexed_earn)
    indexed_earnings.sort()

    tot_indexed_earnings = sum(indexed_earnings[-35:])
    avg_indexed_earnings = tot_indexed_earnings/420.0
    
    bracket1 = min(avg_indexed_earnings, 895.0) * 0.90
    bracket2 = max(min(avg_indexed_earnings - 895.0, 5397.0 - 895.0),0) * 0.32
    bracket3 = max(avg_indexed_earnings - 5397.0, 0.0) * 0.15

    return float(math.floor(bracket1 + bracket2 + bracket3))

def ssn_if_retired_at(age):

    if age == 62: monthly = 2299.0
    if age == 63: monthly = 2463.0
    if age == 64: monthly = 2664.0
    if age == 65: monthly = 2865.0
    if age == 66: monthly = 3095.0
    if age == 67: monthly = 3321.0
    if age == 68: monthly = 3591.0
    if age == 69: monthly = 3861.0
    if age >= 70: monthly = 4135.0

    return 12.0 * monthly
