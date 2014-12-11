"""
    Testing out an object oriented way of how to implement support for other datatypes (like Matrices)
    without breaking the implementation of the Nodex. The idea is to make the Nodex object a lot more
    abstract and extend its use with plug-in datatypes.
"""
from core import Nodex
import nodex.utils
from functools import partial
import pymel.core


class Math(object):
    @staticmethod
    def bimath(self, other, func):
        """ Convenience method for the special methods like __add__, __sub__, etc. """
        return func(self, other)

    sum = partial(nodex.utils.plusMinusAverage, operation=1, name="sum", dimensions=None)
    multiply = partial(nodex.utils.multiplyDivide, operation=1, name="multiply")
    multDouble = partial(nodex.utils.doubleLinear, nodeType="multDoubleLinear", name="multDouble")
    divide = partial(nodex.utils.multiplyDivide, operation=2, name="divide")
    power = partial(nodex.utils.multiplyDivide, operation=3, name="power")
    add = partial(nodex.utils.doubleLinear, nodeType="addDoubleLinear", name="add")
    sum = partial(nodex.utils.plusMinusAverage, dimensions=None, operation=1, name="sum") # TODO: Implement THIS!
    sum1D = partial(nodex.utils.plusMinusAverage, dimensions=1, operation=1, name="sum1D")
    sum2D = partial(nodex.utils.plusMinusAverage, dimensions=2, operation=1, name="sum2D")
    sum3D = partial(nodex.utils.plusMinusAverage, dimensions=3, operation=1, name="sum3D")
    subtract = partial(nodex.utils.plusMinusAverage, dimensions=None, operation=2, name="subtract")
    subtract1D = partial(nodex.utils.plusMinusAverage, dimensions=1, operation=2, name="subtract1D")
    subtract2D = partial(nodex.utils.plusMinusAverage, dimensions=2, operation=2, name="subtract2D")
    subtract3D = partial(nodex.utils.plusMinusAverage, dimensions=3, operation=2, name="subtract3D")
    average1D = partial(nodex.utils.plusMinusAverage, dimensions=1, operation=3, name="average1D")
    average2D = partial(nodex.utils.plusMinusAverage, dimensions=2, operation=3, name="average2D")
    average3D = partial(nodex.utils.plusMinusAverage, dimensions=3, operation=3, name="average3D")
    clamp = partial(nodex.utils.clamp, name="clamp")
    equal = partial(nodex.utils.condition, operation=0, name="equal")
    notEqual = partial(nodex.utils.condition, operation=1, name="notEqual")
    greaterThan = partial(nodex.utils.condition, operation=2, name="greaterThan")
    greaterOrEqual = partial(nodex.utils.condition, operation=3, name="greaterOrEqual")
    lessThan = partial(nodex.utils.condition, operation=4, name="lessThan")
    lessOrEqual = partial(nodex.utils.condition, operation=5, name="lessOrEqual")

# TODO: Implement these methods/nodes (not necessarily in order of importance):
#Nodex.blend (=blendColors)
#Nodex.setRange
#Nodex.contrast
#Nodex.reverse
#Nodex.stencil
#Nodex.overlay (= multiple nodes)
#Nodex.vectorProduct
#Nodex.angleBetween
#Nodex.unitConversion

class Numerical(Nodex):
    _priority = 2

    @staticmethod
    def isValidData(data):

        if isinstance(data, (float, int, bool)):
            return True

        # attribute
        if isinstance(data, pymel.core.Attribute):
            return True
        elif isinstance(data, basestring):
            try:
                pymel.core.Attribute(data)
                return True
            except TypeError:
                # TODO: check if node has a known conversion if so get the default output attribute (this should be extendible)
                data = pymel.core.PyNode(data)
                raise

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


class Array(Nodex):
    """ The array DataType is rather complex since it can hold a variety of DataTypes. """
    _priority = 50


class Matrix(Nodex):
    _priority = 100