#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the parameter_reference module

Also see the doctests in doc/parameters.txt
"""

from __future__ import print_function

import unittest

from parameters.parameter_reference import ParameterReference
from parameters.parameter_set import ParameterSet


class ParameterReferenceTest(unittest.TestCase):
    def test_simple_lazy_evaluation(self):
        p = ParameterReference("A")
        p + 1
        self.assertEqual(p.evaluate({'A': 2, 'dummy': 3}), 3)

    def test_simple_lazy_left(self):
        p = ParameterReference("A")
        p / 10
        self.assertEqual(p.evaluate({'A': 20, 'dummy': 3}), 2)

    def test_simple_lazy_right(self):
        p = ParameterReference("A")
        10 / p
        self.assertEqual(p.evaluate({'A': 5, 'dummy': 3}), 2)

    def test_ParameterSet_value(self):
        ps = ParameterSet({'a': 1, 'b': 2}, label="PS1")
        p = ParameterReference("A")
        self.assertEqual(p.evaluate({'A': ps, 'dummy': 3}), ps)
        p + 1
        self.assertRaises(ValueError, p.evaluate, {'A': ps, 'dummy': 3})

    def test_unsupported_operation(self):
        p = ParameterReference("A")
        p / "string"
        self.assertRaises(TypeError, p.evaluate, {'A': 5, 'dummy': 3})

    def test_replace_references_with_operations(self):
        ps = ParameterSet({
            'p1': 2,
            'p2': 4,
            'p3': ParameterReference('p1')+ParameterReference('p2')+1,
            'p4': ParameterReference('p3')+1,
            'p5': {"z": ParameterReference('p4')+1},
            'p6': ParameterReference('p5')
            })
        ps.replace_references()

        self.assertEqual(ps.p3, 7)
        self.assertEqual(ps.p4, 8)
        self.assertEqual(ps.p6.z, 9)


if __name__ == '__main__':
    unittest.main()
