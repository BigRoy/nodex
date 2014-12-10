"""
    Testing out an object oriented way of how to implement support for other datatypes (like Matrices)
    without breaking the implementation of the Nodex. The idea is to make the Nodex object a lot more
    abstract and extend its use with plug-in datatypes.
"""
from core import PyNodex


class Numerical(PyNodex):
    _priority = 25

    @staticmethod
    def isValidData(data):
        if isinstance(data, (float, int, bool)):
            return True

    def default(self):
        return 0.0

    def dimensions(self):
        return 1

    def convertData(self, data):
        return float(data)


class Boolean(Numerical):
    _priority = 5

    @staticmethod
    def isValidData(data):
        if isinstance(data, bool):
            return True

    def convertData(self, data):
        data = bool(data)


class Integer(Numerical):
    _priority = 10

    @staticmethod
    def isValidData(data):
        if isinstance(data, int):
            return True


class Float(Numerical):
    _priority = 15

    @staticmethod
    def isValidData(data):
        if isinstance(data, float):
            return True


class Array(PyNodex):
    """ The array DataType is rather complex since it can hold a variety of DataTypes. """
    _priority = 50


class Matrix(PyNodex):
    _priority = 100