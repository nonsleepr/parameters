# -*- coding: utf-8 -*-
"""
A sub-class of ParameterSet that can represent a table of parameters.

"""

from __future__ import division, print_function

from parameters.parameter_set import ParameterSet


def _string_table(tablestring):
    """Convert a table written as a multi-line string into a dict of dicts."""
    tabledict = {}
    rows = tablestring.strip().split('\n')
    column_headers = rows[0].split()
    for row in rows[1:]:
        row = row.split()
        row_header = row[0]
        tabledict[row_header] = {}
        for col_header, item in zip(column_headers[1:], row[1:]):
            tabledict[row_header][col_header] = float(item)
    return tabledict


class ParameterTable(ParameterSet):

    """
    A sub-class of `ParameterSet` that can represent a table of parameters.

    i.e., it is limited to one-level of nesting, and each sub-dict must have
    the same keys. In addition to the possible initialisers for ParameterSet,
    a ParameterTable can be initialised from a multi-line string, e.g.::

        >>> pt = ParameterTable('''
        ...     #       col1    col2    col3
        ...     row1     1       2       3
        ...     row2     4       5       6
        ...     row3     7       8       9
        ... ''')
        >>> pt.row2.col3
        6.0
        >>> pt.column('col1')
        {'row1': 1.0, 'row2': 4.0, 'row3': 7.0}
        >>> pt.transpose().col3.row2
        6.0

    """

    non_parameter_attributes = ParameterSet.non_parameter_attributes + \
        ['row', 'rows', 'row_labels',
         'column', 'columns', 'column_labels']

    def __init__(self, initialiser, label=None):
        if hasattr(initialiser, 'lower'):  # url or table string
            tabledict = _string_table(initialiser)
            # if initialiser is a URL, _string_table() should return an empty
            # dict since URLs do not contain spaces.
            if tabledict:  # string table
                initialiser = tabledict
        super(ParameterTable, self).__init__(initialiser, label)
        # Now need to check that the contents actually define a table, i.e.
        # two levels of nesting and each sub-dict has the same keys
        self._check_is_table()

    def rows(self):
        """Return a list of (row_label, row) pairs, as 2-tuples. """
        return self.items()

    def row_labels(self):
        """Return a list of row labels. """
        return self.keys()

    def _check_is_table(self):
        """
        Check that the contents actually define a table.

        i.e. one level of nesting and each sub-dict has the same keys.
        Raises an `Exception` if these requirements are violated.

        """
        # to be implemented
        pass

    def row(self, row_label):
        """Return a `ParameterSet` object containing the requested row."""
        return self[row_label]

    def column(self, column_label):
        """Return a `ParameterSet` object containing the requested column."""
        col = {row_label: row[column_label] for row_label, row in self.rows()}
        return ParameterSet(col)

    def columns(self):
        """Return a list of `(column_label, column)` pairs, as 2-tuples."""
        return [(column_label, self.column(column_label)) for
                column_label in self.column_labels()]

    def column_labels(self):
        """Return a list of column labels."""
        return self[list(self.row_labels())[0]].keys()

    def transpose(self):
        """Return a copy with rows and columns swapped. """
        new_table = ParameterTable({})
        for column_label, column in self.columns():
            new_table[column_label] = column
        return new_table

    def table_string(self):
        """Return the table as a string.

        The string is suitable for being used as the
        initialiser for a new `ParameterTable`.

        """
        # formatting could definitely be improved
        column_labels = self.column_labels()
        lines = ["#\t " + "\t".join(column_labels)]
        for row_label, row in self.rows():
            lines.append(row_label + "\t" + "\t".join(["%s" % row[col] for col
                                                       in column_labels]))
        return "\n".join(lines)
