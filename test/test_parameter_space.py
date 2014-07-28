#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the parameter_space module

Also see the doctests in doc/parameters.txt

"""

from __future__ import print_function

from copy import deepcopy
import os
import types
import unittest

import numpy as np

try:
    import scipy
    have_scipy = True
except ImportError:
    have_scipy = False

from parameters.parameter_range import ParameterRange
from parameters.parameter_set import ParameterSet
from parameters.parameter_space import ParameterSpace

from parameters.distributions import (GammaDist, NormalDist,
                                      ParameterDist, UniformDist)


class ParameterSpaceDotAccess(unittest.TestCase):

    def setUp(self):
        ps7 = ParameterSpace({})
        ps7.name = ParameterSpace({})
        ps7.x = ParameterRange([1, 2])
        self.yrange = [1.1, 2.2]
        ps7.name.y = ParameterRange(self.yrange)
        ps7.foo = ParameterSet({})

        self.ps7 = ps7

    def test_valid_access(self):
        ps7 = self.ps7
        self.assertEqual(ps7.name.y, ps7['name.y'])
        ps7['foo.bar'] = 10.0
        assert ps7['foo'].bar == ps7.foo.bar == ps7.foo['bar']

    def test_invalid_access(self):
        # names cannot have a dot in them unless the name
        # before the dot is already defined.
        # Another functionality possibility would be to
        # automagically and implicitly do ps7.foo = ParameterSet({}) here
        # but that doesn't warn the user of typos.
        ps7 = self.ps7

        def f(k, v):
            ps7[k] = v
        self.assertRaises(KeyError, f, 'bar.foo', 10.0)


class ParameterSpaceIterationTest(unittest.TestCase):

    def setUp(self):
        ps7 = ParameterSpace({})
        ps7.name = ParameterSpace({})
        ps7.x = ParameterRange([1, 2])
        self.yrange = [1.1, 2.2]
        ps7.name.y = ParameterRange(self.yrange)
        ps7.foo = ParameterSet({})
        self.ps7 = ps7

    def test_iter_inner(self):
        ps7 = self.ps7
        assert [x.name.y for x in ps7.iter_range_key('name.y')] == self.yrange
        out = [(1, 1.1000000000000001), (1, 2.2000000000000002),
               (2, 1.1000000000000001), (2, 2.2000000000000002)]
        out1 = [(1, 1.1000000000000001), (2, 1.1000000000000001),
                (1, 2.2000000000000002), (2, 2.2000000000000002)]
        out2 = [(ps.x, ps.name.y) for ps in ps7.iter_inner()]
        assert out2 in (out, out1)

    def test_is_ref_by_default(self):
        # check that we're returning only many versions of the same
        # object by default
        ps7 = self.ps7
        out = [x for x in ps7.iter_inner()]
        assert np.alltrue([x == out[0] for x in out])

    def test_returns_ParameterSet(self):
        ps7 = self.ps7
        out = [x for x in ps7.iter_inner()]
        assert isinstance(ps7, ParameterSpace)
        assert isinstance(out[0], ParameterSet)
        assert not isinstance(out[0], ParameterSpace), "%s %s %s" % (
            out[0].pretty(), out[0]._is_space(), type(out[0]))

    def test_copy(self):
        ps7 = self.ps7
        out = [x for x in ps7.iter_inner(copy=True)]
        # now check that there are no duplicate objects
        assert np.alltrue([out[x-1] not in out[x:] for x in range(1,
                                                                  len(out))])

    def test_tree_copy(self):
        ps7 = self.ps7
        ps8 = ps7.tree_copy()
        ps8.x._values[0] = 2
        self.assertEqual(ps8.x, ps7.x)

    def test_num_conditions(self):
        ps7 = self.ps7
        self.assertEqual(ps7.num_conditions(), 4)
        self.assertEqual(ps7.num_conditions(),
                         len([x for x in ps7.iter_inner()]))

    def test_parameter_space_index(self):
        ps7 = self.ps7
        results_dim, results_label = ps7.parameter_space_dimension_labels()
        self.assertEqual(results_dim, [2, 2])
        self.assertEqual(results_label, ['name.y', 'x'])
        indices = [ps7.parameter_space_index(experiment)
                   for experiment in ps7.iter_inner()]
        self.assertEqual(indices, [(0, 0), (0, 1), (1, 0), (1, 1)])
        self.assertEqual(
            ps7.parameter_space_index(
                ParameterSet({'x': 2, 'foo': {}, 'name': {'y': 1.1}})), (0, 1))
        self.assertRaises(ValueError,
                          ps7.parameter_space_index,
                          ParameterSet({'x': 3, 'foo': {},
                                        'name': {'y': 1.1}}))


class ParameterSpaceWithDistributionsTest(unittest.TestCase):

    def setUp(self):
        ps = ParameterSpace({})
        ps.g = GammaDist()
        ps.l = [NormalDist(), UniformDist(), 'a string']
        ps.d = ParameterSpace({'g2': UniformDist(),
                               'x': 0})
        self.ps = ps

    def test_dist_keys(self):
        self.assertEqual(set(self.ps.dist_keys()), set(['g', 'l', 'd.g2']))

    @unittest.skipUnless(have_scipy, "SciPy not available")
    def test_realize_dists_with_copy_True(self):
        gen = self.ps.realize_dists(n=2, copy=True)
        assert isinstance(gen, types.GeneratorType)
        output = list(gen)
        # for item in output:
        #    print item.pretty()
        self.assertEqual(len(output), 2)
        self.assertNotEqual(output[0].g, output[1].g)
        self.assertEqual(output[0].d.x, output[1].d.x)
        self.assertNotEqual(output[0].l[0], output[1].l[0])
        self.assertNotEqual(output[0].l[1], output[1].l[1])
        self.assertEqual(output[0].l[2], output[1].l[2])

    @unittest.skipUnless(have_scipy, "SciPy not available")
    def test_realize_dists_with_copy_False(self):
        gen = self.ps.realize_dists(n=2, copy=False)
        assert isinstance(gen, types.GeneratorType)
        output = []
        for item in gen:
            output.append(deepcopy(item))
        self.assertEqual(len(output), 2)
        self.assertNotEqual(output[0].g, output[1].g)
        self.assertEqual(output[0].d.x, output[1].d.x)
        self.assertNotEqual(output[0].l[0], output[1].l[0])
        self.assertNotEqual(output[0].l[1], output[1].l[1])
        self.assertEqual(output[0].l[2], output[1].l[2])


class ParameterSpaceSaveLoadTest(unittest.TestCase):

    def setUp(self):
        psp = ParameterSpace({})
        psp.g = GammaDist()
        psp.l = [NormalDist(), UniformDist(), 'a string']
        psp.d = ParameterSpace({'g2': UniformDist(),
                               'x': 0})
        psp.name = ParameterSpace({})
        psp.x = ParameterRange([1, 2])
        self.yrange = [1.1, 2.2]
        psp.name.y = ParameterRange(self.yrange)
        psp.foo = ParameterSet({})
        self.psp = psp

    def tearDown(self):
        if os.path.exists('test.param'):
            os.remove('test.param')

    def test_save_and_load(self):
        my_url = "file://%s/test.param" % os.getcwd()
        self.psp.save(my_url)
        new_psp = ParameterSpace(my_url)
        self.assertEqual(self.psp, new_psp)
        self.assertEqual(self.psp.g, new_psp.g)


# class ParameterSpaceWithBothRangesAndDists(unittest.TestCase):
#
#    def setUp(self):
#        psp = ParameterSpace({})
#        psp.g = GammaDist()
#        psp.l = [NormalDist(), UniformDist(), 'a string']
#        psp.d = ParameterSpace({'g2': UniformDist(),
#                               'x': 0})
#        psp.name = ParameterSpace({})
#        psp.x = ParameterRange([1,2])
#        self.yrange = [1.1,2.2]
#        psp.name.y = ParameterRange(self.yrange)
#        psp.foo = ParameterSet({})
#        self.psp = psp
#
#    def test_iter_inner(self):
#        psp = self.psp
#        for pst in psp.iter_inner():
#            print pst.pretty()


if __name__ == '__main__':
    unittest.main()
