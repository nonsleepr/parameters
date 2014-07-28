# -*- coding: utf-8 -*-
"""A class for representing/managing hierarchical parameter sets. """

from __future__ import division, print_function

import math
import os
import os.path

try:
    # Python 2
    from urllib2 import build_opener, install_opener, ProxyHandler, urlopen
    from urlparse import urlparse
except ImportError:
    # Python 3
    from urllib.request import (build_opener, install_opener,
                                ProxyHandler, urlopen)
    from urllib.parse import urlparse

from parameters.parameter_range import ParameterRange
from parameters.parameter_reference import ParameterReference
from parameters.distributions import (GammaDist, NormalDist, ParameterDist,
                                      UniformDist)


if 'HTTP_PROXY' in os.environ:
    HTTP_PROXY = os.environ['HTTP_PROXY']  # user has to define it
    ''' next lines are for communication to urllib of proxy information '''
    proxy_support = ProxyHandler({"https": HTTP_PROXY})
    opener = build_opener(proxy_support, HTTPHandler)
    install_opener(opener)


def _nesteddictwalk(d, separator='.'):
    """
    Walk a nested dict structure, using a generator.

    Composite keys are created by joining each key to the key of the parent
    dict using `separator`.

    """
    for key1, value1 in d.items():
        if isinstance(value1, dict):
            for key2, value2 in _nesteddictwalk(value1, separator):
                # recurse into subdict
                yield "%s%s%s" % (key1, separator, key2), value2
        else:
            yield key1, value1


def _nesteddictflatten(d, separator='.'):
    """
    Return a flattened version of a nested dict structure.

    Composite keys are created by joining each key to the key of the parent
    dict using `separator`.

    """
    flatd = {}
    for k, v in _nesteddictwalk(d, separator):
        flatd[k] = v
    return flatd


def load_parameters(parameter_url, modified_parameters):
    """
    The function that should be used to load a ParameterSet from a url.

    `modified_parameters` should be a dictionary of parameters and their
    values. These will be replaced in the loaded parameter set before the
    references are expanded.

    """
    parameters = ParameterSet(parameter_url)
    parameters.replace_values(**modified_parameters)
    parameters.replace_references()
    return parameters


class ParameterSet(dict):

    """
    A class to manage hierarchical parameter sets.

    Usage example::

        >>> sim_params = ParameterSet({'dt': 0.1, 'tstop': 1000.0})
        >>> path = "http://neuralensemble.org/svn/NeuroTools/example.params"
        >>> exc_cell_params = ParameterSet(path)
        >>> inh_cell_params = ParameterSet({'tau_m': 15.0, 'cm': 0.5})
        >>> network_params = ParameterSet({'excitatory_cells': exc_cell_params,
        ...                                'inhibitory_cells':
        ...                                inh_cell_params})
        >>> P = ParameterSet({'sim': sim_params, 'network': network_params})
        >>> P.sim.dt
        0.1
        >>> P.network.inhibitory_cells.tau_m
        15.0
        >>> print P.pretty()

    """

    non_parameter_attributes = ['_url', 'label', 'names', 'parameters', 'flat',
                                'flatten', 'non_parameter_attributes']
    invalid_names = ['parameters', 'names']  # should probably add dir(dict)

    @staticmethod
    def read_from_str(s, update_namespace=None):
        """
        Read a `ParameterSet` from a str.

        `ParameterSet` definition `s` should be a Python dict definition
        string, containing objects of types `int`, `float`, `str`, `list`,
        `dict` plus the classes defined in this module, `Parameter`,
        `ParameterRange`, etc.  No other object types are allowed,
        except the function `url('some_url')` or `ref('point.delimited.path')`,
        e.g.::

            {'a': {'A': 3, 'B': 4},
             'b': [1,2,3],
             'c': 'hello world',
             'd': url('http://example.com/my_cool_parameter_set')
             'e': ref('level1_param_name.level2_param_name.level3_param_name')}

        This is largely the JSON (www.json.org) format, but with
        extra keywords in the namespace such as `ParameterRange`, `GammaDist`,
        etc.

        """
        # initialize these now to avoid import loops
        from parameters.parameter_table import ParameterTable

        global_dict = dict(ref=ParameterReference,
                           url=ParameterSet,
                           ParameterSet=ParameterSet,
                           ParameterRange=ParameterRange,
                           ParameterTable=ParameterTable,
                           GammaDist=GammaDist,
                           UniformDist=UniformDist,
                           NormalDist=NormalDist,
                           pi=math.pi,
                           true=True,    # these are for reading JSON
                           false=False,  # files
                           )
        if update_namespace:
            global_dict.update(update_namespace)

        d = None
        try:
            if 'file://' in s:
                path = s.split('file://')[1]
                ifile = open(path, 'r')
                content = ifile.read()
                ifile.close()
                d = eval(content, global_dict)
            else:
                d = eval(s, global_dict)
        except SyntaxError as e:
            raise SyntaxError(
                "Invalid string for ParameterSet definition: %s\n%s" % (s, e))
        except TypeError as e:
            raise SyntaxError(
                "Invalid string for ParameterSet definition: %s" % e)
        return d or {}

    @staticmethod
    def check_validity(k):
        """Docstring missing. """
        if k in ParameterSet.invalid_names:
            raise Exception("'%s' is not allowed as a parameter name." % k)

    def __init__(self, initialiser, label=None, update_namespace=None):
        def walk(d, label):
            # Iterate through the dictionary `d`, replacing `dict`s by
            # `ParameterSet` objects.
            for k, v in d.items():
                ParameterSet.check_validity(k)
                if isinstance(v, ParameterSet):
                    d[k] = v
                elif isinstance(v, dict):
                    d[k] = walk(v, k)
                else:
                    d[k] = v
            return ParameterSet(d, label)

        self._url = None
        if hasattr(initialiser, 'lower'):  # url or str
            if os.path.exists(initialiser):
                f = open(initialiser, 'r')
                pstr = f.read()
                self._url = initialiser
                f.close()
            else:
                try:
                    f = urlopen(initialiser)
                    pstr = f.read().decode()
                    self._url = initialiser
                except IOError:
                    pstr = initialiser
                    self._url = None
                else:
                    f.close()

            # is it a yaml url?
            if self._url:
                o = urlparse(self._url)
                base, ext = os.path.splitext(o.path)
                if ext in ['.yaml', '.yml']:
                    import yaml
                    initialiser = yaml.load(pstr)
                else:
                    initialiser = ParameterSet.read_from_str(pstr,
                                                             update_namespace)
            else:
                initialiser = ParameterSet.read_from_str(pstr,
                                                         update_namespace)

        # By this stage, `initialiser` should be a dict. Iterate through it,
        # copying its contents into the current instance, and replacing dicts
        # by ParameterSet objects.
        if isinstance(initialiser, dict):
            for k, v in initialiser.items():
                ParameterSet.check_validity(k)
                if isinstance(v, ParameterSet):
                    self[k] = v
                elif isinstance(v, dict):
                    self[k] = walk(v, k)
                else:
                    self[k] = v
        else:
            raise TypeError("`initialiser` must be a `dict`, a `ParameterSet` "
                            "object, a string, or a valid URL")

        # Set the label
        if hasattr(initialiser, 'label'):
            # if initialiser was a ParameterSet,
            # keep the existing label if the label arg is None
            self.label = label or initialiser.label
        else:
            self.label = label

        # Define some aliases, allowing, e.g.:
        # for name, value in P.parameters():
        # for name in P.names():
        self.names = self.keys
        self.parameters = self.items

    def flat(self):
        return _nesteddictwalk(self)

    flat.__doc__ = _nesteddictwalk.__doc__

    def flatten(self):
        return _nesteddictflatten(self)

    flatten.__doc__ = _nesteddictflatten.__doc__

    def __getattr__(self, name):
        """Allow accessing parameters using dot notation. """
        try:
            return self[name]
        except KeyError:
            return self.__getattribute__(name)

    def __setattr__(self, name, value):
        """Allow setting parameters using dot notation. """
        if name in self.non_parameter_attributes:
            object.__setattr__(self, name, value)
        else:
            # should we check the parameter type hasn't changed?
            self[name] = value

    def __getitem__(self, name):
        """Modified get that detects dots '.' in the names.

        Goes down the nested tree to find it.

        """
        split = name.split('.', 1)
        if len(split) == 1:
            return dict.__getitem__(self, name)
        # nested get
        return dict.__getitem__(self, split[0])[split[1]]

    def flat_add(self, name, value):
        """`__setitem__`that adds `ParameterSet({})` objects to the namespace.

        This is only done if necessary.

        """
        split = name.split('.', 1)
        if len(split) == 1:
            dict.__setitem__(self, name, value)
        else:
            # nested set
            try:
                ps = dict.__getitem__(self, split[0])
            except KeyError:
                # setting nested name without parent existing
                # create parent
                ps = ParameterSet({})
                dict.__setitem__(self, split[0], ps)
                # and try again
            ps.flat_add(split[1], value)

    def __setitem__(self, name, value):
        """ Modified set that detects dots '.' in the names.

        It goes down the nested tree to set it.

        """
        split = name.split('.', 1)
        if len(split) == 1:
            dict.__setitem__(self, name, value)
        else:
            # nested set
            dict.__getitem__(self, split[0])[split[1]] = value

    def update(self, E, **kwargs):
        """Docstring missing. """
        if hasattr(E, "has_key"):
            for k in E:
                self[k] = E[k]
        else:
            for (k, v) in E:
                self[k] = v
        for k in kwargs:
            self[k] = kwargs[k]

    # should __len__() be the usual dict length, or the flattened length?
    # Probably the former for consistency with dicts
    # can always use len(ps.flatten())

    # what about __contains__()? Should we drill down to lower levels in the
    # hierarchy? I think so.

    def __getstate__(self):
        """For pickling."""
        return self

    def save(self, url=None, expand_urls=False):
        """
        Write the parameter set to a text file.

        The text file syntax is open to discussion. My idea is that it should
        be valid Python code, preferably importable as a module.

        If `url` is `None`, try to save to `self._url` (if it is not `None`),
        otherwise save to `url`.

        """
        # possible solution for HTTP PUT: http://inamidst.com/proj/put/put.py
        if not url:
            url = self._url
        assert url != ''
        if not self._url:
            self._url = url
        scheme, netloc, path, parameters, query, fragment = urlparse(url)
        if scheme == 'file' or (scheme == '' and netloc == ''):
            f = open(path, 'w')
            f.write(self.pretty(expand_urls=expand_urls))
            f.close()
        else:
            if scheme:
                raise Exception(
                    "Saving using the %s protocol is not implemented" % scheme)
            else:
                raise Exception("No protocol (http, ftp, etc) specified.")

    def pretty(self, indent='  ', expand_urls=False):
        """
        Return a unicode string of the structure of the `ParameterSet`.

        Evaluating the string should recreate the object.

        """
        def walk(d, indent, ind_incr):
            s = []
            for k, v in d.items():
                if hasattr(v, 'items'):
                    if expand_urls is False and hasattr(v, '_url') and v._url:
                        s.append('%s"%s": url("%s"),' % (indent, k, v._url))
                    else:
                        s.append('%s"%s": {' % (indent, k))
                        s.append(walk(v, indent+ind_incr,  ind_incr))
                        s.append('%s},' % indent)
                elif hasattr(v, 'lower'):
                    s.append('%s"%s": "%s",' % (indent, k, v))
                else:
                    # what if we have a dict or ParameterSet inside a list?
                    # currently they are not expanded. Should they be?
                    s.append('%s"%s": %s,' % (indent, k, v))
            return '\n'.join(s)
        return '{\n' + walk(self, indent, indent) + '\n}'

    def tree_copy(self):
        """Return a copy of the `ParameterSet` tree structure.

        Nodes are not copied, but re-referenced.

        """
        # initialize these now to avoid import loops
        from parameters.parameter_space import ParameterSpace

        tmp = ParameterSet({})
        for key in self:
            value = self[key]
            if isinstance(value, ParameterSet):
                tmp[key] = value.tree_copy()
            elif isinstance(value, ParameterReference):
                tmp[key] = value.copy()
            else:
                tmp[key] = value
        if tmp._is_space():
            tmp = ParameterSpace(tmp)
        return tmp

    def as_dict(self):
        """Return a copy of the `ParameterSet` structure as a nested dict. """
        tmp = {}

        for key in self:
            value = self[key]
            if isinstance(value, ParameterSet):
                # recurse
                tmp[key] = value.as_dict()
            else:
                tmp[key] = value
        return tmp

    def __sub__(self, other):
        """
        Return the difference between this `ParameterSet` and another.

        Not yet properly implemented.

        """
        self_keys = set(self)
        other_keys = set(other)
        intersection = self_keys.intersection(other_keys)
        difference1 = self_keys.difference(other_keys)
        difference2 = other_keys.difference(self_keys)
        result1 = dict([(key, self[key]) for key in difference1])
        result2 = dict([(key, other[key]) for key in difference2])
        # Now need to check values for intersection....
        for item in intersection:
            if isinstance(self[item], ParameterSet):
                d1, d2 = self[item] - other[item]
                if d1:
                    result1[item] = d1
                if d2:
                    result2[item] = d2
            elif self[item] != other[item]:
                result1[item] = self[item]
                result2[item] = other[item]
        if len(result1) + len(result2) == 0:
            assert self == other, "Error in ParameterSet.diff()"
        return result1, result2

    def _is_space(self):
        """
        Check for the presence of `ParameterRanges` or `ParameterDists`.

        Determines if this is a `ParameterSet` or a `ParameterSpace`.

        """
        for k, v in self.flat():
            if isinstance(v, ParameterRange) or isinstance(v, ParameterDist):
                return True
        return False

    def export(self, filename, format='latex', **kwargs):
        """Docstring missing. """
        if format == 'latex':
            from .export import parameters_to_latex
            parameters_to_latex(filename, self, **kwargs)

    def replace_references(self):
        while True:
            refs = self.find_references()
            if len(refs) == 0:
                break
            for s, k, v in refs:
                s[k] = v.evaluate(self)

    def find_references(self):
        l = []
        for k, v in self.items():
            if isinstance(v, ParameterReference):
                l += [(self, k, v)]
            elif isinstance(v, ParameterSet):
                l += v.find_references()
        return l

    def replace_values(self, **args):
        """
        The arguments must be in the form path=value.

        Path should be a . (dot) delimited path to a parameter in the parameter
        tree rooted in this ParameterSet instance.

        This function replaces the values of each parameter in the args with
        the corresponding values supplied in the arguments.

        """
        for k in args.keys():
            self[k] = args[k]
