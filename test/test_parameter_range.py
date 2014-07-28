#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the parameter_range module

Also see the doctests in doc/parameters.txt

"""

from __future__ import print_function

import unittest

from parameters.parameter_range import ParameterRange


try:
    next                  # Python 3
except NameError:
    def next(obj):        # Python 2
        return obj.next()


class ParameterRangeTest(unittest.TestCase):

    def test_simple_create(self):
        pr = ParameterRange([1, 3, 5, 7, 9], units="mV", name="test")
        values = []
        for x in pr:
            values.append(x)
        self.assertEqual(values, [1, 3, 5, 7, 9])

    def test_shuffle_create(self):
        input_values = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
        pr = ParameterRange(input_values, units="mV", name="test",
                            shuffle=True)
        values = []
        for x in pr:
            values.append(x)
        # will occasionally, by chance, fail
        self.assertNotEqual(values, input_values)
        self.assertEqual(set(values), set(input_values))

    def test_str_and_repr(self):
        pr = ParameterRange([1, 3, 5, 7, 9], units="mV", name="pr")
        self.assertEqual(repr(pr),
                         'ParameterRange([1, 3, 5, 7, 9], units="mV")')
        first_value = next(pr)
        self.assertEqual(str(first_value), '1')

    def test_invalid_create(self):
        self.assertRaises(TypeError, ParameterRange, 555, name="invalid")


if __name__ == '__main__':
    unittest.main()
