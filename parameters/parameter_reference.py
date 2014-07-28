# -*- coding: utf-8 -*-
"""
A class to specify a parameter in terms of the value of another parameter.

"""

from __future__ import division, print_function

from functools import wraps
import operator


def _reverse(func):
    """Given a function f(a, b), returns f(b, a). """
    @wraps(func)
    def reversed_func(a, b):
        return func(b, a)
    reversed_func.__doc__ = "Reversed argument form of %s" % func.__doc__
    reversed_func.__name__ = "reversed %s" % func.__name__
    return reversed_func


def _lazy_operation(name, reversed=False):
    def op(self, val):
        f = getattr(operator, name)
        if reversed:
            f = _reverse(f)
        self.operations.append((f, val))
        return self
    return op


class ParameterReference(object):

    """
    A class that provides a place-holder for a reference parameter.

    The reference parameter will later be replaced with the value of the
    parameter pointed to by the reference.
    This class also allows for lazy application of operations,
    meaning that one can use the reference in simple formulas that will get
    evaluated at the moment the reference is replaced.

    Check below which operations are supported.

    """

    def __init__(self, reference):
        object.__init__(self)
        self.reference_path = reference
        self.operations = []

    def _apply_operations(self, x):
        for f, arg in self.operations:
            try:
                if arg is None:
                    x = f(x)
                else:
                    x = f(x, arg)
            except TypeError:
                raise TypeError("ParameterReference: error applying operation "
                                "%s with argument %s to %s" % (f, arg, x))
        return x

    def evaluate(self, parameter_set):
        """
        Evaluate the reference.

        It uses the ParameterSet in parameter_set as the source.

        """
        from parameters.parameter_set import ParameterSet

        ref_value = parameter_set[self.reference_path]
        if isinstance(ref_value, ParameterSet):
            if self.operations == []:
                return ref_value.tree_copy()
            else:
                raise ValueError("ParameterReference: lazy operations cannot "
                                 "be applied to argument of type ParameterSet>"
                                 " %s" % self.reference_path)
        elif isinstance(ref_value, ParameterReference):
            # lets wait until the refe
            return self
        else:
            return self._apply_operations(ref_value)

    def copy(self):
        pr = ParameterReference(self.reference_path)
        for f, arg in self.operations:
            if isinstance(arg, ParameterReference):
                pr.operations.append((f, arg.copy()))
            else:
                pr.operations.append((f, arg))
        return pr

    __add__ = _lazy_operation('add')
    __radd__ = __add__
    __sub__ = _lazy_operation('sub')
    __rsub__ = _lazy_operation('sub', reversed=True)
    __mul__ = _lazy_operation('mul')
    __rmul__ = __mul__
    __div__ = _lazy_operation('div')
    __rdiv__ = _lazy_operation('div', reversed=True)
    __truediv__ = _lazy_operation('truediv')
    __rtruediv__ = _lazy_operation('truediv', reversed=True)
    __pow__ = _lazy_operation('pow')
