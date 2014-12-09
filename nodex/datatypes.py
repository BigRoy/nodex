"""
    Testing out an object oriented way of how to implement support for other datatypes (like Matrices)
    without breaking the implementation of the Nodex. The idea is to make the Nodex object a lot more
    abstract and extend its use with plug-in datatypes.
"""

import abc


class DataTypeBase(object):
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
    def get(self):
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

    @abc.abstractmethod
    def default(self):
        """
        :return: Default value for this datatype. The returned type must be something that can be validly converted by
                 this datatype in 'self.convertReference'
        """
        pass


class Array(DataTypeBase):
    """ The array DataType is rather complex since it can hold a variety of DataTypes. """


class Numerical(DataTypeBase):
    pass


class Integer(Numerical):
    pass


class Float(Numerical):
    pass


class Boolean(Numerical):
    pass


class Matrix(DataTypeBase):
    pass