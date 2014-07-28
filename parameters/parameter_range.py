# -*- coding: utf-8 -*-
"""A class for specifying a list of possible values for a given parameter. """

from __future__ import division, print_function

from copy import copy
import random

from parameters.parameter import Parameter, _isiterable


try:
    next                  # Python 3
except NameError:
    def next(obj):        # Python 2
        return obj.next()


class ParameterRange(Parameter):

    """
    A class for specifying a list of possible values for a given parameter.

    The value must be an iterable. It acts like a Parameter, but .next() can be
    called to iterate through the values
    """

    def __init__(self, value, units=None, name="", shuffle=False):
        if not _isiterable(value):
            raise TypeError("A ParameterRange value must be iterable")
        Parameter.__init__(self, next(value.__iter__()), units, name)
        self._values = copy(value)
        self._iter_values = self._values.__iter__()
        if shuffle:
            random.shuffle(self._values)

    def __repr__(self):
        units_str = ''
        if self.units:
            units_str = ', units="%s"' % self.units
        return 'ParameterRange(%s%s)' % (self._values.__repr__(), units_str)

    def __iter__(self):
        self._iter_values = self._values.__iter__()
        return self._iter_values

    def __next__(self):
        self._value = next(self._iter_values)
        return self._value

    def next(self):
        return self.__next__()

    def __len__(self):
        return len(self._values)

    def __eq__(self, o):
        if (type(self) == type(o) and
            self.name == o.name and
            self._values == o._values and
                self.units == o.units):
            return True
        else:
            return False
