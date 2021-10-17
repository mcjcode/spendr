#/usr/bin/env python
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
    min_age=1000
    max_age=0
    
    with open(fn) as fp:
        line = fp.readline()
        while line.startswith('#'):
            line = fp.readline()

        age_str, pd_str = line.split(',')
        age = int(age_str)
        pd = float(pd_str)
        max_age = max(max_age,age)
        min_age = min(min_age,age)
        h[age] = pd

    def f(age):
        if age > max_age:
            age = max_age
        return h[age]

    return f
