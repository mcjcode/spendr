#!/usr/bin/env python

import ssn
import earnings

test_earnings = earnings.load_earnings('earnings.csv')
index_factors = ssn.index_factors('ssn_index_factors_1954.csv')
full_benefit = ssn.calc_full_benefit(test_earnings, index_factors)

