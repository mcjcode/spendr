#!/usr/bin/env python
#
# mortality.py
#

from collections import defaultdict

#
# sample usage:
#
# mortality_function_from_table('552.csv')
#
# 552 is from 1990 for Males
#
def mortality_function_from_table(fn):
    with open(fn,'rb') as fp:
        line = fp.readline()
        while not line.startswith(b"Row\Column"):
            line = fp.readline()

        h = defaultdict(lambda:1.0)
        for line in fp:
            fields = line.split(b',')
            year = int(fields[0])
            rate = float(fields[1])
            h[year] = rate

    def f(year):
        return h[year]

    return f
