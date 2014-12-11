"""
    Testing out an object oriented way of how to implement support for other datatypes (like Matrices)
    without breaking the implementation of the Nodex. The idea is to make the Nodex object a lot more
    abstract and extend its use with plug-in datatypes.
"""
from core import Nodex, Math
import nodex.utils
from functools import partial
import pymel.core


class Numerical(Nodex):
    _priority = 25

    @staticmethod
    def validateAttr(attr):
        if attr.isArray() or attr.isCompound():
            return False
        return True

    @staticmethod
    def isValidData(data):

        if isinstance(data, (float, int, bool)):
            return True

        # attribute
        if isinstance(data, pymel.core.Attribute):
            return Numerical.validateAttr(data)
        elif isinstance(data, basestring):
            try:

                attr = pymel.core.Attribute(data)
                if Numerical.validateAttr(attr):
                    return True

            except TypeError:
                # TODO: check if node has a known conversion if so get the default output attribute (this should be extendible)
                data = pymel.core.PyNode(data)
                raise

        return False

    def default(self):
        return 0.0

    def dimensions(self):
        return 1

    def convertData(self, data):
        if isinstance(data, (float, int, bool)):
            return data

        # attribute
        if isinstance(data, pymel.core.Attribute):
            return data
        elif isinstance(data, basestring):
            try:
                return pymel.core.Attribute(data)
            except TypeError:
                # TODO: check if node has a known conversion if so get the default output attribute (this should be extendible)
                data = pymel.core.PyNode(data)
                raise

        raise TypeError("Can't convert {0}".format(data))

    def __calc(self, other, func):

        return func(self, other)

    # region special methods override: mathematical operators
    def __add__(self, other):
        return Math.bimath(self, other, func=Math.sum)

    def __sub__(self, other):
        return Math.bimath(self, other, func=Math.subtract)

    def __mul__(self, other):
        return Math.bimath(self, other, func=Math.multiply)

    def __xor__(self, other):
        return Math.bimath(self, other, func=Math.power)

    def __pow__(self, other):
        return Math.bimath(self, other, func=Math.power)

    def __div__(self, other):
        return Math.bimath(self, other, func=Math.divide)
    #endregion

    # region special methods override: rich-comparisons-methods

    def __eq__(self, other):
        return Math.bimath(self, other, func=Math.equal)

    def __ne__(self, other):
        return Math.bimath(self, other, func=Math.notEqual)

    def __gt__(self, other):
        return Math.bimath(self, other, func=Math.greaterThan)

    def __ge__(self, other):
        return Math.bimath(self, other, func=Math.greaterOrEqual)

    def __lt__(self, other):
        return Math.bimath(self, other, func=Math.lessThan)

    def __le__(self, other):
        return Math.bimath(self, other, func=Math.lessOrEqual)

    # endregion


class Boolean(Numerical):
    _priority = 5

    @staticmethod
    def isValidData(data):
        if isinstance(data, bool):
            return True

        return False

    def convertData(self, data):
        data = bool(data)

    @staticmethod
    def default():
        return False


class Integer(Numerical):
    _priority = 10

    @staticmethod
    def isValidData(data):
        if isinstance(data, int):
            return True

        return False

    @staticmethod
    def default():
        return 0


class Float(Numerical):
    _priority = 15

    @staticmethod
    def isValidData(data):
        if isinstance(data, float):
            return True

        return False

    @staticmethod
    def default():
        return 0.0


class Array(Nodex):
    """ The array DataType is rather complex since it can hold a variety of DataTypes. """
    _priority = 50

    @staticmethod
    def validateAttr(attr):
        if attr.isArray() or attr.isCompound():
            return True
        return False

    @staticmethod
    def isValidData(data):

        # attribute
        if isinstance(data, pymel.core.Attribute):
            return Array.validateAttr(data)
        elif isinstance(data, basestring):
            try:
                attr = pymel.core.Attribute(data)
                return Array.validateAttr(attr)
            except RuntimeError:
                return False

        # list
        elif isinstance(data, (list, tuple)):
            if len(data) == 0:
                return False
            return True

        return False

    def convertData(self, data):

        if isinstance(data, pymel.core.Attribute):
            return data
        elif isinstance(data, basestring):
            return pymel.core.Attribute(data)

        if isinstance(data, (tuple, list)):
            # Convert any references internal to the array
            data = tuple(Nodex(x) for x in data)
            # Validate every element has max single dimension of depth
            if any(x.dimensions() > 1 for x in data):
                raise ValueError("Can't create an Array type of Nodex that nests attributes/values with a "
                                 "higher dimension than one.")
            return data

        raise TypeError()


    # region special methods override: mathematical operators
    def __add__(self, other):
        return Math.bimath(self, other, func=Math.sum)

    def __sub__(self, other):
        return Math.bimath(self, other, func=Math.subtract)

    def __mul__(self, other):
        return Math.bimath(self, other, func=Math.multiply)

    def __xor__(self, other):
        return Math.bimath(self, other, func=Math.power)

    def __pow__(self, other):
        return Math.bimath(self, other, func=Math.power)

    def __div__(self, other):
        return Math.bimath(self, other, func=Math.divide)
    #endregion

    # region special methods override: rich-comparisons-methods

    def __eq__(self, other):
        return Math.bimath(self, other, func=Math.equal)

    def __ne__(self, other):
        return Math.bimath(self, other, func=Math.notEqual)

    def __gt__(self, other):
        return Math.bimath(self, other, func=Math.greaterThan)

    def __ge__(self, other):
        return Math.bimath(self, other, func=Math.greaterOrEqual)

    def __lt__(self, other):
        return Math.bimath(self, other, func=Math.lessThan)

    def __le__(self, other):
        return Math.bimath(self, other, func=Math.lessOrEqual)
    # endregion



class Vector(Nodex):
    # TODO: Implement vector math (cross-product, dot-product)
    _priority = 1000

class Matrix(Nodex):
    # TODO: Implement matrix math
    _priority = 1001