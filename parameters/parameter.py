# -*- coding: utf-8 -*-
"""A base class for all parameter-type objects. """

from __future__ import division, print_function


def _isiterable(x):
    return hasattr(x, '__iter__') and not hasattr(x, 'lower')


class Parameter(object):

    """A base class for all parameter-type objects. """

    def __init__(self, value, units=None, name=""):
        self.name = name
        self.value = value
        self.units = units
        self.type = type(value)

    def __repr__(self):
        s = "%s = %s" % (self.name, self.value)
        if self.units is not None:
            s += " %s" % self.units
        return s
