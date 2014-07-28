#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the parameter_set module

Also see the doctests in doc/parameters.txt

"""

from __future__ import print_function

import os
import pickle
import types
import unittest

from parameters.parameter_reference import ParameterReference
from parameters.parameter_set import ParameterSet


class ParameterSetCreateTest(unittest.TestCase):

    def test_create_from_dict(self):
        ps = ParameterSet({'a': 1, 'b': 2}, label="PS1")
        ps2 = ParameterSet({'ps': ps, 'c': 19}, label="PS2")
        ps3 = ParameterSet({'hello': 'world', 'ps2': ps2, 'null': None,
                            'true': False, 'mylist': [1, 2, 3, 4],
                            'mydict': {'c': 3, 'd': 4},
                            'yourlist': [1, 2, {'e': 5, 'f': 6}],
                            }, label="PS3")
        ps4 = ParameterSet(ps)
        ps5 = ParameterSet(ps, label="PS5")
        ps6 = ParameterSet(ps3)
        assert isinstance(ps3, ParameterSet)
        assert isinstance(ps3.ps2, ParameterSet)
        assert isinstance(ps3['ps2'].ps, ParameterSet)
        assert isinstance(ps3.ps2.ps.a, int)
        assert isinstance(ps3.mydict, ParameterSet)
        assert ps3.ps2.label == "PS2"
        assert ps3.mydict.label == 'mydict'
        assert isinstance(ps4, ParameterSet)
        assert ps4.label == ps.label, "%s != %s" % (ps4.label, ps.label)
        assert ps5.label == "PS5"

    def test_create_from_string(self):
        ps1 = ParameterSet("{'a': 1, 'b':2}")
        ps2 = ParameterSet({'a': 1, 'b': 2})
        self.assertEqual(ps1, ps2)

    def test_create_from_flat_iterator(self):
        ps = ParameterSet({'a': 1, 'b': 2}, label="PS1")
        ps2 = ParameterSet({'ps': ps, 'c': 19}, label="PS2")
        ps3 = ParameterSet({'hello': 'world', 'ps2': ps2, 'null': None,
                            'true': False, 'mylist': [1, 2, 3, 4],
                            'mydict': {'c': 3, 'd': 4},
                            'yourlist': [1, 2, {'e': 5, 'f': 6}],
                            }, label="PS3")
        ps4 = ParameterSet({})
        for x in ps3.flat():
            ps4.flat_add(x[0], x[1])
        self.assertEqual(ps4, ps3)

    def test_create_with_syntax_error(self):
        self.assertRaises(SyntaxError, ParameterSet, "{'a': 1, 'b':2")

    def test_create_with_NameError(self):
        self.assertRaises(NameError, ParameterSet, "{a: 1, b:2}")

    def test_create_with_invalid_initialiser(self):
        self.assertRaises(TypeError, ParameterSet, object)

    def test_create_yaml_url(self):
        import tempfile
        import yaml

        conf1_str = """
        # user info
        username: joe
        email:  joe@example.com

        # recipes
        recipes:
           all: /somewhere1/file1.xml
           specific: /somewhere2/file2.xml
        """
        ps = ParameterSet
        tf = tempfile.NamedTemporaryFile(suffix='.yaml', mode='w')
        tf.file.writelines(conf1_str)
        tf.file.flush()
        tf.file.seek(0)
        ps = ParameterSet("file://" + tf.name)
        tf.close()
        ps1 = ParameterSet(yaml.load(conf1_str))
        assert ps1 == ps

    def test_create_with_references(self):
        ps = ParameterSet({'hello': 'world',
                           'ps2': {
                               'ps': {'a': 1, 'b': 2},
                               'c': 19
                               },
                           'null': None,
                           'true': False,
                           'mylist': [1, 2, 3, 4],
                           'mydict': {'c': 3, 'd': 4},
                           'yourlist': [1, 2, {'e': 5, 'f': 6}],
                           'ref1': ParameterReference('null'),
                           'ref2': ParameterReference('ps2.ps.b'),
                           'nested_refs': {
                               'ref3': ParameterReference('mydict.d'),
                           }
                           })
        ps.replace_references()
        self.assertEqual(ps.ref1, None)
        self.assertEqual(ps.ref2, 2)
        self.assertEqual(ps.nested_refs.ref3, 4)


class ParameterSetSaveLoadTest(unittest.TestCase):

    def setUp(self):
        ps = ParameterSet({'a': 1, 'b': 2}, label="PS1")
        ps2 = ParameterSet({'ps': ps, 'c': 19}, label="PS2")
        self.ps = ParameterSet({'hello': 'world', 'ps2': ps2, 'null': None,
                                'true': False, 'mylist': [1, 2, 3, 4],
                                'mydict': {'c': 3, 'd': 4},
                                'yourlist': [1, 2, {'e': 5, 'f': 6}],
                                }, label="PS3")

    def tearDown(self):
        if os.path.exists('test.param'):
            os.remove('test.param')

    def test_save_and_load(self):
        my_url = "file://%s/test.param" % os.getcwd()
        self.ps.save(my_url)
        new_ps = ParameterSet(my_url)
        self.assertEqual(self.ps, new_ps)
        self.assertEqual(self.ps.ps2.ps.b, new_ps.ps2.ps.b)
        # for now, labels are not preserved on saving
        # self.assertEqual(self.ps.label, new_ps.label)

    def test_pickle(self):
        pkl = pickle.dumps(self.ps)
        new_ps = pickle.loads(pkl)
        self.assertEqual(self.ps, new_ps)
        self.assertEqual(self.ps.ps2.ps.b, new_ps.ps2.ps.b)
        # self.assertEqual(self.ps.label, new_ps.label) # or on pickling


class ParameterSetFlattenTest(unittest.TestCase):

    def setUp(self):
        ps = ParameterSet({'a': 1, 'b': 2}, label="PS1")
        ps2 = ParameterSet({'ps': ps, 'c': 19}, label="PS2")
        self.ps = ParameterSet({'hello': 'world', 'ps2': ps2, 'null': None,
                                'true': False, 'mylist': [1, 2, 3, 4],
                                'mydict': {'c': 3, 'd': 4},
                                'yourlist': [1, 2, {'e': 5, 'f': 6}],
                                }, label="PS3")

    def test_flatten(self):
        assert isinstance(self.ps.flatten(), dict)
        self.assertEqual(self.ps.flatten(),
                         {'null': None, 'mylist': [1, 2, 3, 4], 'ps2.ps.b': 2,
                          'mydict.c': 3, 'mydict.d': 4,
                          'yourlist': [1, 2, {'e': 5, 'f': 6}], 'ps2.c': 19,
                          'true': False, 'hello': 'world', 'ps2.ps.a': 1})

    def test_flat(self):
        self.assertEqual(types.GeneratorType, type(self.ps.flat()))
        D = {}
        for k, v in self.ps.flat():
            D[k] = v
        self.assertEqual(D, self.ps.flatten())


class ParameterSetMiscTest(unittest.TestCase):

    def setUp(self):
        ps = ParameterSet({'a': 1, 'b': 2}, label="PS1")
        ps2 = ParameterSet({'ps': ps, 'c': 19}, label="PS2")
        self.ps = ParameterSet({'hello': 'world', 'ps2': ps2, 'null': None,
                                'true': False, 'mylist': [1, 2, 3, 4],
                                'mydict': {'c': 3, 'd': 4},
                                'yourlist': [1, 2, {'e': 5, 'f': 6}],
                                }, label="PS3")

    def test_as_dict(self):
        self.assertEqual(self.ps.as_dict(),
                         {'hello': 'world',
                          'ps2': {'ps': {'a': 1, 'b': 2}, 'c': 19},
                          'null': None,
                          'true': False,
                          'mylist': [1, 2, 3, 4],
                          'mydict': {'c': 3, 'd': 4},
                          'yourlist': [1, 2, {'e': 5, 'f': 6}],
                          })


class ParameterSetDiffTest(unittest.TestCase):

    def setUp(self):
        ps = ParameterSet({'a': 1, 'b': 2}, label="PS1")
        ps2 = ParameterSet({'ps': ps, 'c': 19}, label="PS2")
        self.ps = ParameterSet({'hello': 'world', 'ps2': ps2, 'null': None,
                                'true': False, 'mylist': [1, 2, 3, 4],
                                'mydict': {'c': 3, 'd': 4},
                                'yourlist': [1, 2, {'e': 5, 'f': 6}],
                                }, label="PS3")

    def test_diff_self_is_zero(self):
        self.assertEqual(self.ps - self.ps, ({}, {}))

    def test_diff_at_top_level(self):
        ps2 = ParameterSet(self.ps.as_dict())
        ps2.hello = 'universe'
        self.assertEqual(ps2 - self.ps, ({'hello': 'universe'},
                                         {'hello': 'world'}))
        self.assertEqual(self.ps - ps2, ({'hello': 'world'},
                                         {'hello': 'universe'}))

    def test_diff_as_bottom_level(self):
        ps2 = ParameterSet(self.ps.as_dict())
        ps2.ps2.ps.b = 3
        self.assertEqual(ps2 - self.ps, ({'ps2': {'ps': {'b': 3}}},
                                         {'ps2': {'ps': {'b': 2}}}))

    def test_diff_inside_list(self):
        ps2 = ParameterSet(self.ps.as_dict())
        ps2.yourlist = [100, 2, {'e': 55, 'f': 6}]
        self.assertEqual(ps2 - self.ps,
                         ({'yourlist': [100, 2, {'e': 55, 'f': 6}]},
                          {'yourlist': [1, 2, {'e': 5, 'f': 6}]}))


if __name__ == '__main__':
    unittest.main()
