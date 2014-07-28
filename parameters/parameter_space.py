# -*- coding: utf-8 -*-
"""
A class for a collection of ParameterSets.

Represents multiple points in a parameter space.

"""

from __future__ import division, print_function

from parameters.parameter import _isiterable
from parameters.parameter_range import ParameterRange
from parameters.parameter_set import ParameterSet
from parameters.distributions import ParameterDist


def _contains_instance(collection, cls):
    return any(isinstance(o, cls) for o in collection)


class ParameterSpace(ParameterSet):

    """
    A collection of `ParameterSets`.

    Represents multiple points in parameter space.

    Created by putting `ParameterRange` and/or `ParameterDist`
    objects within a `ParameterSet`.

    """

    def iter_range_key(self, range_key):
        """
        An iterator of the `ParameterSpace`.

        Yields the `ParameterSet` with the `ParameterRange` given by
        `range_key` replaced with each of its values

        """
        for val in self[range_key]:
            tmp = self.tree_copy()
            tmp[range_key] = val
            yield tmp

    def iter_inner_range_keys(self, keys, copy=False):
        """
        An iterator of the `ParameterSpace`.

        Yields `ParameterSets` with all combinations of `ParameterRange`
        elements which are given by the `keys` list.

        Note: each newly yielded value is one and the same object
        so storing the returned values results in a collection
        of many of the lastly yielded object.

        `copy=True` causes each yielded object to be a newly
        created object, but be careful because this is
        spawning many dictionaries!

        """
        if len(keys) == 0:
            # return an iterator over 1 copy for modifying
            yield self.tree_copy()
            return

        # recursively iterate over remaining keys
        for tmp in self.iter_inner_range_keys(keys[1:]):
            # iterator over range of our present attention
            for val in self[keys[0]]:
                if copy:
                    tmp = tmp.tree_copy()
                tmp[keys[0]] = val
                if not tmp._is_space():
                    tmp = ParameterSet(tmp)
                yield tmp

    def range_keys(self):
        """Return the list of keys for elements that are `ParameterRanges`. """
        return [key for key, value in self.flat()
                if isinstance(value, ParameterRange)]

    def iter_inner(self, copy=False):
        """An iterator of the `ParameterSpace`.

        Yields `ParameterSets` with all combinations of `ParameterRange`
        elements.

        """
        return self.iter_inner_range_keys(self.range_keys(), copy)

    def num_conditions(self):
        """Return the number items that will be returned by `iter_inner()`. """
        # Not properly tested
        return prod(len(self[key]) for key in self.range_keys())

    def dist_keys(self):
        """Return the list of keys for elements which are `ParameterDists`. """
        def is_or_contains_dist(value):
            return (isinstance(value, ParameterDist) or
                    (_isiterable(value) and
                     _contains_instance(value, ParameterDist)))
        return [key for key, value in self.flat()
                if is_or_contains_dist(value)]

    def realize_dists(self, n=1, copy=False):
        """
        For each `ParameterDist` realize the distribution and yield the result.

        If `copy==True`, causes each yielded object to be a newly
        created object, but be careful because this is
        spawning many dictionaries!

        """
        def next(item, n):
            if isinstance(item, ParameterDist):
                return item.next(n)
            else:
                return [item]*n
        # pre-generate random numbers
        rngs = {}
        for key in self.dist_keys():
            if _isiterable(self[key]):
                rngs[key] = [next(item, n) for item in self[key]]
            else:
                rngs[key] = self[key].next(n)

            # get a copy to fill in the rngs
            tmp = self.tree_copy()
            for i in range(n):
                for key in rngs:
                    if _isiterable(self[key]):
                        tmp[key] = [rngs[key][j][i]
                                    for j in range(len(rngs[key]))]
                    else:
                        tmp[key] = rngs[key][i]
                yield tmp.tree_copy() if copy else tmp

    def parameter_space_dimension_labels(self):
        """
        Return the dimensions and labels of the keys of `ParameterRanges`.

        `range_keys` are sorted to ensure the same ordering each time.

        """
        range_keys = sorted(self.range_keys())
        label = [len(getattr(self, key)) for key in range_keys]

        return range_keys, label

    def parameter_space_index(self, current_experiment):
        """
        Return the index of the current experiment.

        The index is in the dimension of the parameter space :
        i.e. parameter space dimension: [2,3]
        i.e. index: (1,0)

        Example::

            p = ParameterSet({})
            p.b = ParameterRange([1,2,3])
            p.a = ParameterRange(['p','y','t','h','o','n'])

            results_dim, results_label = p.parameter_space_dimension_labels()

            results = numpy.empty(results_dim)
            for experiment in p.iter_inner():
                index = p.parameter_space_index(experiment)
                results[index] = 2.

        """
        index = []
        range_keys = sorted(self.range_keys())
        for key in range_keys:
            value = getattr(current_experiment, key)
            try:
                value_index = list(getattr(self, key)._values).index(value)
            except ValueError:
                raise ValueError("The ParameterSet provided is not within the "
                                 "ParameterSpace")
            index.append(value_index)
        return tuple(index)

    def get_ranges_values(self):
        """
        Return a dict with the keys and values of the  `ParameterRanges`.

        Example::

            >>> p = ParameterSpace({})
            >>> p.b = ParameterRange([1,2,3])
            >>> p.a = ParameterRange(['p','y','t','h','o','n'])
            >>> data = p.get_ranges_values()
            >>> data
            {'a': ['p', 'y', 't', 'h', 'o', 'n'], 'b': [1, 2, 3]}

        """
        return {key: getattr(self, key)._values for
                key in sorted(self.range_keys())}
