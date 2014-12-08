"""
    Testing out an object oriented way of how to implement support for other datatypes (like Matrices)
    without breaking the implementation of the Nodex. The idea is to make the Nodex object a lot more
    abstract and extend its use with plug-in datatypes.
"""

import abc

class DataType(object):
    """
        Each DataType represents a reference type for a Nodex.
        eg. Boolean, Numerical,
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, reference):
        if not self.isValid(reference):
            raise TypeError("Not a valid reference type for datatype {0}".format(self.__class__.__name__))
        self._reference = reference

    @abc.abstractmethod
    def isValid(self, reference):
        pass

    @abc.abstractmethod
    def set(self, v):
        """ Assign a value to the reference
        """
        pass

    @abc.abstractmethod
    def get(self, v):
        """
        :param v:
        :return:
        """
        return self._data

    @abc.abstractmethod
    def asAttribute(self):
        """ Creates a node that holds the reference data's value as a constant within an Attribute and returns the
            connectable Attribute as a Nodex. """
        pass

    @abc.abstractmethod
    def dimensions(self):
        pass


class Array(DataType):
    """ The array DataType is rather complex since it can hold a variety of DataTypes. """


class Numerical(DataType):
    pass


class Integer(Numerical):
    pass


class Float(Numerical):
    pass


class Boolean(Numerical):
    pass


class Matrix(DataType):
    pass