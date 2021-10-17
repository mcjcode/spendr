#!/usr/bin/env python
#
# returns.py
#

import numpy as np


def normal(mu,sigma):
    while True:
        yield np.random.normal()*sigma + mu


def garch11(mu,alpha,beta,sigma2):
    while True:
        e = np.random.normal()*np.sqrt(sigma2)
        yield e + mu
        sigma2 = alpha*sigma2 + beta*e*e
