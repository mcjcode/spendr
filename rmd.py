#!/usr/bin/env python
#
# rmd.py
#
# code for required minimum distributions
#

rmd_start_age = 72.0
    

def uniform_life_expectancy(fn):
    """
    fn: filename containing ULE data
    returns: function returning ULE at each age
    """
    h = {}
    max_age: int = 0
    
    with open(fn) as fp:
        line = fp.readline()
        while line.startswith('#'):
            line = fp.readline()

        age_str, pd_str = line.split(',')
        age = int(age_str)
        pd = float(pd_str)
        max_age = max(max_age, age)
        h[age] = pd

    def _ule(withdrawal_age):
        return h[min(withdrawal_age, max_age)]

    return _ule
