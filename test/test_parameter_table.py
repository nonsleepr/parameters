#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the parameter_table module

Also see the doctests in doc/parameters.txt

"""

from __future__ import print_function

import unittest

from parameters.parameter_set import ParameterSet
from parameters.parameter_table import ParameterTable


class ParameterTableTest(unittest.TestCase):

    def test_create_from_string(self):
        pt = ParameterTable('''
            #       col1    col2    col3
            row1     1       2       3
            row2     4       5       6
            row3     7       8       9
        ''')
        assert isinstance(pt, ParameterSet)
        self.assertEqual(pt.row2.col3, 6.0)
        self.assertEqual(pt.column('col1'),
                         {'row1': 1.0, 'row2': 4.0, 'row3': 7.0})
        self.assertEqual(pt.row('row2'),
                         {'col1': 4.0, 'col2': 5.0, 'col3': 6.0})
        self.assertEqual(pt.transpose().col3.row2, 6.0)

    def test_table_string(self):
        pt = ParameterTable('''
            #       col1    col2    col3
            row1     1       2       3
            row2     4       5       6
            row3     7       8       9
        ''')
        ts = pt.table_string()
        self.assertEqual(pt, ParameterTable(ts))
        self.assertNotEqual(pt, ParameterTable(ts.replace('7', '8')))


if __name__ == '__main__':
    unittest.main()
