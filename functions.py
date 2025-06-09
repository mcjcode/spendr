#!/usr/bin/env python
import numpy as np


class PLIF(object):
    """
    PLIF (Piecewise Linear Increasing Function).
    Implemented because we want to be able to compute
    the inverse of such functions efficiently w/o doing
    numerical search.
    """
    def compose(self, other):
        """
        :param other: another PLIF
        :return: the composition of self with other, so that the evaluation of
        the composition is first applying self and then applying other.
        """
        self_inv = self.inverse()
        xs2 = [self_inv(x) for x in other.xs]
        xs = list(np.unique(sorted(self.xs + xs2)))
        ys = [other(self(x)) for x in xs]
        return PLIF(xs, ys)

    def xshift(self, x0):
        """
        Return a new PLIF g so that g(x) = self(x-x0)

        :param x0: the x offset.
        :return: a new function.
        """
        xs = [x-x0 for x in self.xs]
        ys = list(self.ys)
        return PLIF(xs, ys)

    def __init__(self, xs, ys):
        x1 = xs[0]
        for x2 in xs[1:]:
            if x1 >= x2:
                raise ValueError(f'x-values are not increasing xs={xs}, ys={ys}')
            x1 = x2            
        self.xs = list(xs)
        y1 = ys[0]
        for y2 in ys[1:]:
            if y1 >= y2:
                raise ValueError(f'y-values are not increasing xs={xs}, ys={ys}')
        self.ys = list(ys)

    def __call__(self, x):
        n = len(self.xs)
        if x < self.xs[0]:
            slope = (self.ys[1] - self.ys[0])/(self.xs[1]-self.xs[0])
            return self.ys[0] - slope * (self.xs[0] - x)
        for i in range(1, n):
            if x < self.xs[i]:
                # self.xs[i-1] <= x < self.xs[i]
                r = (x-self.xs[i-1])/(self.xs[i]-self.xs[i-1])
                return self.ys[i-1] + r * (self.ys[i] - self.ys[i-1])
        slope = (self.ys[n-1]-self.ys[n-2])/(self.xs[n-1] - self.xs[n-2])
        return self.ys[n-1] + slope * (x - self.xs[n-1])

    def inverse(self):
        """
        The inverse of a PLIF is a PLIF.
        """
        other = PLIF(self.ys, self.xs)
        return other
    
    def __add__(self, other):
        """
        The sum of two PLIFs is a PLIF and the sum of a PLIF
        with a number is a PLIF
        """
        if type(other) == PLIF:
            xs = sorted(np.unique(list(set(self.xs + other.xs))))
            ys = [self(x) + other(x) for x in xs]
        elif type(other) in [int, float]:
            xs = list(self.xs)
            ys = [y+other for y in self.ys]
        else:
            raise TypeError(f'A PLIF can only be added with a PLIF or a number.  type(other)={type(other)}')
        return PLIF(xs, ys)

    def __mul__(self, other):
        if type(other) in [int, float]:
            if other > 0:
                xs = list(self.xs)
                ys = [x*other for x in xs]
            else:
                raise ValueError(f'Can only multiply a PLIF by a positive number. other={other}')
        else:
            raise TypeError(f'Can only multiply a PLIF by a number. type(other)={type(other)}')
        return PLIF(xs, ys)

    







        
