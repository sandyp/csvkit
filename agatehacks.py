import agate
from decimal import Decimal


def to_one_place(d):
    return d.quantize(Decimal('0.1'))


class Percent(agate.Computation):
    """
    Computes a column's percentage of a total
    """
    def __init__(self, column_name, total=None):
        self._column_name = column_name
        self._total = total

    def get_computed_data_type(self, table):
        return agate.Number()

    def validate(self, table):
        column = table.columns[self._column_name]
        if not isinstance(column.data_type, agate.Number):
            raise agate.DataTypeError('Percent column must contain Number data.')
        if self._total is not None and self._total <= 0:
            raise agate.DataTypeError('The total must be a positive number')
        # Throw a warning if there are nulls in there
        if agate.HasNulls(self._column_name).run(table):
            agate.warn_null_calculation(self, column)
          
    def run(self, table):
        """
        :returns:
            :class:`decimal.Decimal`
        """
        # If the user has provided a total, use that
        if self._total is not None:
            total = self._total
        # Otherwise compute the sum of all the values in that column to
        # act as our denominator
        else:
            total = table.aggregate(agate.Sum(self._column_name))
            # Raise error if sum is less than or equal to zero
            if total <= 0:
                raise agate.DataTypeError('The sum of column values must be a positive number')

        # Create a list new rows
        new_column = []
        # Loop through the existing rows
        for row in table.rows:
            # Pull the value
            value = row[self._column_name]
            if value is None:
                new_column.append(None)
                continue
            # Try to divide it out of the total
            percent = value / total
            # And multiply it by 100
            percent = percent * 100
            # Append the value to the new list
            new_column.append(to_one_place(percent))
        # Pass out the list
        return new_column