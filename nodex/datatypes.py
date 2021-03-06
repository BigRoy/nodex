"""
    The datatypes supported by the Nodex factory are defined by subclasses of the Nodex that validate the data
    and convert the input data when required.

    By looking at the datatype documentation you're able to have a look at what methods/functionality they provide.
"""

# standard library
import itertools
import logging
logger = logging.getLogger(__name__)

# maya library
import pymel.core
import pymel.core.datatypes
import maya.OpenMaya
import maya.api.OpenMaya
import maya.cmds

# local library
import nodex.utils
from core import Nodex, Math

# TODO: It's possibly simpler to remove the either convertData or isValidData method and create a single method that
#       will return converted data but raise an InvalidDataError if it doesn't. This will reduce code duplicity, plus
#       is likely a tiny bit faster.


class Numerical(Nodex):
    """ The Numerical datatype is the base class for all single numerical values (eg. `Float`, `Integer`, `Boolean`).

        .. note:: Currently this is also the class that will be instantiated when reference an attribute of a single
                  numerical value (since Float/Integer/Boolean haven't been implemented like that as of yet).
                  Nevertheless all those classes should behave as expected.
    """
    _priority = 25

    _attr_types = frozenset(["int", "float", "bool", "double", "doubleAngle", "time",
                           "doubleLinear", "long", "short", "byte", "enum", ])

    @staticmethod
    def validateAttr(attr):
        if attr.isArray() or attr.isCompound():
            return False

        if attr.type() in Numerical._attr_types:
            return True

        return False

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
        """ (+ operator) Add to the other `Nodex` using + """
        return Math.bimath(self, other, func=Math.sum)

    def __sub__(self, other):
        """ Subtract the other `Nodex` from this instance using - """
        return Math.bimath(self, other, func=Math.subtract)

    def __mul__(self, other):
        """ Multiply the other `Nodex` with this instance using * """
        return Math.bimath(self, other, func=Math.multiply)

    def __xor__(self, other):
        """ Square this instance by other `Nodex` using ^ """
        return Math.bimath(self, other, func=Math.power)

    def __pow__(self, other):
        """ Square this instance by other `Nodex` using pow() """
        return Math.bimath(self, other, func=Math.power)

    def __div__(self, other):
        """ Divide this instance by other `Nodex` using / """
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

    def abs(self, **kwargs):
        """ Returns the absolute value of this value.

            :rtype: :class:`nodex.datatypes.Float`
        """
        return Math.abs(self, **kwargs)

    def sign(self, **kwargs):
        """ Returns whether this value is greater or equal to zero.

            :rtype: :class:`nodex.datatypes.Float`
        """
        return Math.greaterOrEqual(self, 0.0)
    # endregion


class Boolean(Numerical):
    """
        The `Boolean` datatype represents a single True/False value where the given data is either a Python `bool`
        if it's referencing a value or a maya boolean attribute if it references an attribute.
    """
    _priority = 5

    @staticmethod
    def isValidData(data):
        if isinstance(data, bool):
            return True

        return False

    def convertData(self, data):
        data = bool(data)
        return data

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
    """ The `Array` datatype is rather complex since itself holds elements that are converted to other datatypes.

        The `Array` can only hold elements with a dimension of one. So it will not hold a nested list.
    """
    _priority = 100

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

            # This is relatively slow... but hey, let's keep it for now (should be mergeable with below)
            if any(Nodex(x).dimensions() > 1 for x in data):
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

    def default(self):
        # TODO: This is supposed to be a staticmethod, but that won't work on the Array
        #       Because we don't want to have 'empty' Nodex Arrays.
        return tuple(x.default() for x in self._data)

    # region special methods override: mathematical operators
    def __add__(self, other):
        """ Add all individual components of this array to the other Nodex """
        return Math.bimath(self, other, func=Math.sum)

    def __sub__(self, other):
        """ Subtract all individual components of this array by the other Nodex """
        return Math.bimath(self, other, func=Math.subtract)

    def __mul__(self, other):
        """ Multiply all individual components of this array with the other Nodex """
        return Math.bimath(self, other, func=Math.multiply)

    def __xor__(self, other):
        """ Square all individual components of this array by the other Nodex """
        return Math.bimath(self, other, func=Math.power)

    def __pow__(self, other):
        """ Square all individual components of this array by the other Nodex """
        return Math.bimath(self, other, func=Math.power)

    def __div__(self, other):
        """ Divide all individual components of this array by the other Nodex """
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

    def abs(self, **kwargs):
        return Math.abs(self, **kwargs)


class Vector(Array):
    """
        Vectorsssss
    """
    _priority = 50
    _allowed_iterables = (tuple, list)
    _attr_types = frozenset(["reflectance", "reflectanceRGB", "spectrum", "spectrumRGB",
                             "float3", "double3", "long3"])

    @staticmethod
    def validateAttr(attr):
        if attr.isArray() or attr.isCompound():
            if nodex.utils.attrDimensions(attr) == 3:
                return True

        if attr.type() in Vector._attr_types:
            return True

        return False

    @staticmethod
    def isValidData(data):

        # attribute
        if isinstance(data, pymel.core.Attribute):
            return Vector.validateAttr(data)
        elif isinstance(data, basestring):
            attr = pymel.core.Attribute(data)
            return Vector.validateAttr(attr)

        # matrix data
        elif isinstance(data, (pymel.core.datatypes.Vector, pymel.core.datatypes.FloatVector,
                               maya.OpenMaya.MVector, maya.OpenMaya.MFloatVector,
                               maya.api.OpenMaya.MVector, maya.api.OpenMaya.MFloatVector)):
            return True

        # list, like [0, 0, 0]
        elif isinstance(data, Matrix._allowed_iterables) and len(data) == 3:
            return True

        return False

    def convertData(self, data):
        # region attribute
        if isinstance(data, pymel.core.Attribute):
            if Vector.validateAttr(data):
                return data
        elif isinstance(data, basestring):
            data = pymel.core.Attribute(data)
            if Vector.validateAttr(data):
                return data
        # endregion

        # region array-data
        # convert maya.OpenMaya, maya.api.OpenMaya or pymel.core.datatypes Vectors
        elif isinstance(data, (pymel.core.datatypes.Vector, pymel.core.datatypes.FloatVector,
                          maya.OpenMaya.MVector, maya.OpenMaya.MFloatVector,
                          maya.api.OpenMaya.MVector, maya.api.OpenMaya.MFloatVector)):
            data = tuple(data)

        # convert list to tuple
        elif isinstance(data, list):
            data = tuple(data)

        return super(Vector, self).convertData(data)
        # endregion

    def dimensions(self):
        # The dimensions of a Matrix should always be 16, so we assume it for now
        # If one wants a 3x3 Matrix implementation one needs to define a new datatype.
        return 3

    def value(self):
        v = super(Vector, self).value()
        return pymel.core.datatypes.Vector(v)

    @staticmethod
    def default():
        return pymel.core.datatypes.Vector()

    @staticmethod
    def _distanceBetween(point1=None, point2=None, **kwargs):

        name = kwargs.get('name', 'distanceBetween')
        n = pymel.core.createNode("distanceBetween", name=name)

        if point1 is not None:
            Nodex(point1).connect(n.attr('point1'))
        if point2 is not None:
            Nodex(point2).connect(n.attr('point2'))

        return Nodex(n.attr('distance'))

    @staticmethod
    def _vectorProduct(input1=None, input2=None, matrix=None, operation=None, normalizeOutput=None, **kwargs):

        name = kwargs.get('name', 'vectorProduct')
        n = pymel.core.createNode("vectorProduct", name=name)

        if operation is not None:
            n.attr('operation').set(operation)

        if input1 is not None:
            Nodex(input1).connect(n.attr('input1'))
        if input2 is not None:
            Nodex(input2).connect(n.attr('input2'))

        if matrix is not None: # used for operations: Vector Matrix Product and Point Matrix Product
            Nodex(matrix).connect(n.attr('matrix'))

        if normalizeOutput is not None and normalizeOutput is not False:
            Nodex(normalizeOutput).connect(n.attr('normalizeOutput'))

        return Nodex(n.attr('output'))

    @staticmethod
    def _angleBetween(vector1=None, vector2=None, angle=None, axis=None, euler=None, chainAttr='angle', **kwargs):

        name = kwargs.get('name', 'angleBetween')
        n = pymel.core.createNode("angleBetween", name=name)

        # inputs
        if vector1 is not None:
            Nodex(vector1).connect(n.attr('vector1'))
        if vector2 is not None:
            Nodex(vector2).connect(n.attr('vector2'))

        # outputs
        if angle is not None:
            Nodex(n.attr('angle')).connect(angle)
        if axis is not None:
            Nodex(n.attr('axisAngle.axis')).connect(axis)
        if euler is not None:
            Nodex(n.attr('euler')).connect(euler)

        return Nodex(n.attr(chainAttr))

    def cross(self, other, normalizeOutput=False):
        """ Returns the cross product of this and another `Vector`.

        :param other: The other vector
        :type other: :class:`nodex.datatypes.Vector`
        :param normalizeOutput: If True normalizes the output Vector.
        :type normalizeOutput: :class:`nodex.datatypes.Float`
        :return: The cross product
        :rtype: :class:`nodex.datatypes.Vector`
        """
        return self._vectorProduct(self, other, operation=2, normalizeOutput=normalizeOutput, name="vectorCross")

    def dot(self, other, normalizeOutput=False):
        """ Returns the dot product of this and another `Vector`.

        :param other: The other vector
        :type other: :class:`nodex.datatypes.Vector`
        :param normalizeOutput: If True normalizes the output Vector.
        :type normalizeOutput: :class:`nodex.datatypes.Float`
        :return: The dot product
        :rtype: :class:`nodex.datatypes.Vector`
        """
        output = self._vectorProduct(self, other, operation=1, normalizeOutput=normalizeOutput, name="vectorDot")
        # The dot product only results in one value, so get the outputX
        return Nodex(output.node().attr('outputX'))

    def length(self):
        """ Returns the magnitude of the vector.

            :rtype: :class:`nodex.datatypes.Float`"""
        output = self._distanceBetween(self, point2=(0, 0, 0), name="vectorLength")
        output.node().attr('point2').lock()     # lock this input to ensure output stays correct
        return output

    def squareLength(self):
        """ Returns the square length of this `Vector`.

            :rtype: :class:`nodex.datatypes.Float`"""
        v = self ^ [2.0, 2.0, 2.0]          # square all components
        v = Math.sum1D(v[0], v[1], v[2])    # sum all components
        return v

    def distanceTo(self, other):
        """ Returns the distance between this and another `Vector`.

            :rtype: :class:`nodex.datatypes.Float`
        """
        return self._distanceBetween(self, other)

    def angleTo(self, other, angle=None, axis=None, euler=None, chainAttr='angle'):
        """ Returns the angle between this and another `Vector`.

            :rtype: :class:`nodex.datatypes.Float`
        """
        return self._angleBetween(self, other, angle=angle, axis=axis, euler=euler, chainAttr=chainAttr)

    def normal(self):
        """ Return the normalized `Vector`.

            :rtype: :class:`nodex.datatypes.Vector`
        """
        output = self._vectorProduct(self, input2=None, operation=0, normalizeOutput=True, name="vectorNormalize")
        output.node().attr('input2').lock()     # lock this input since it's not being used anyway
        return output


class Matrix(Array):
    """
        Will you take the red or blue pill?

        The Matrix datatype can be initialized by:

            - `maya.OpenMaya.MMatrix` and `maya.OpenMaya.MFloatMatrix`
            - `maya.api.OpenMaya.MMatrix` and `maya.api.OpenMaya.MFloatmatrix`
            - `pymel.core.datatypes.Matrix` and `pymel.core.datatypes.FloatMatrix`
            - list/tuple of 16 elements ``[1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]``
            - or a nested listed of 4x4. ``[[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]``

        Unlike the `Array` datatype the Matrix can be initialized with a nested list/tuple (representing a 4x4 matrix).

        .. note:: Some methods on the Matrix datatype will try to quietly load the `matrixNodes` plug-in (built-in with
                  Maya) ensure the required nodes are available.
    """
    _plugins = ["matrixNodes"]
    _allowed_iterables = (tuple, list)

    # TODO: Implement matrix math
    _priority = 60

    @staticmethod
    def validateAttr(attr):
        """ Workaround for strange Attribute behaviour

        There seems to be a bug in pymel (Maya 2015) where getting the type of a matrix attribute, eg. worldMatrix[0]
        just after creating a node (when attribute hasn't been used yet) will result in 'attr.type()' returning
        None. Nevertheless maya.cmds.getAttr(attr, type=1) returns 'matrix' correctly.

        .. note:: After using maya.cmds.getAttr(attr, type=1) once on that attribute it will somehow behave correctly
                  in pymel as well.

        Then there's also the nitpicky behaviour of Matrix attributes that Maya will never give you the type of the
        attribute unless it's been set before. Otherwise it'll result in 'None' as type.
        (eg. This happens on multMatrix.matrixIn[0])

        :type attr: pymel.core.Attribute
        """
        if isinstance(attr, pymel.core.Attribute):
            attr_name = attr.name()

            # workaround for worldMatrix[0] on transforms
            t = maya.cmds.getAttr(attr_name, type=1)

            if t is None:
                # workaround for matrixIn[0] on multMatrix
                try:
                    attr.set(pymel.core.datatypes.Matrix(), type="matrix")
                except RuntimeError:
                    return False
                t = maya.cmds.getAttr(attr_name, type=1)

            return t == 'matrix'
        return False

    @staticmethod
    def isValidData(data):

        # attribute
        # TODO: Check what the actual type of a Matrix attribute is and implement support
        if isinstance(data, pymel.core.Attribute):
            return Matrix.validateAttr(data)
        elif isinstance(data, basestring):
            attr = pymel.core.Attribute(data)
            return Matrix.validateAttr(attr)

        # matrix data
        elif isinstance(data, (pymel.core.datatypes.Matrix, pymel.core.datatypes.FloatMatrix,
                               maya.OpenMaya.MMatrix, maya.OpenMaya.MFloatMatrix,
                               maya.api.OpenMaya.MMatrix, maya.api.OpenMaya.MFloatMatrix)):
            return True

        # list, like [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        elif isinstance(data, Matrix._allowed_iterables) and len(data) == 16:
            return True

        # nested list, like: [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        elif isinstance(data, Matrix._allowed_iterables) and len(data) == 4 and \
                all(isinstance(x, Matrix._allowed_iterables) and len(x) == 4 for x in data):
            return True

        return False

    def convertData(self, data):
        # Convert the data to a matrix type
        # If the data refers to a Matrix attribute we store the reference directly.
        # Else we store the data as a tuple so we can also hold mixed references like the normal Array datatype.

        # region attribute
        if isinstance(data, pymel.core.Attribute):
            if Matrix.validateAttr(data):
                return data
        elif isinstance(data, basestring):
            data = pymel.core.Attribute(data)
            if Matrix.validateAttr(data):
                return data
        # endregion

        # region array-data
        # flatten nested list
        if isinstance(data, Matrix._allowed_iterables) and len(data) == 4 and \
           all(isinstance(x, Matrix._allowed_iterables) and len(x) == 4 for x in data):
            data = tuple(itertools.chain.from_iterable(data))

        # convert and flatten maya.OpenMaya or pymel matrix
        elif isinstance(data, (pymel.core.datatypes.Matrix, pymel.core.datatypes.FloatMatrix,
                               maya.OpenMaya.MMatrix, maya.OpenMaya.MFloatMatrix)):
            data = tuple(itertools.chain.from_iterable(data))

        # convert maya.api.OpenMaya matrix
        elif isinstance(data, (maya.api.OpenMaya.MMatrix, maya.api.OpenMaya.MFloatMatrix)):
            data = tuple(data)

        # convert list to tuple
        elif isinstance(data, list):
            data = tuple(data)

        return super(Matrix, self).convertData(data)
        # endregion

    def dimensions(self):
        # The dimensions of a Matrix should always be 16, so we assume it for now
        # If one wants a 3x3 Matrix implementation one needs to define a new datatype.
        return 16

    def value(self):
        v = super(Matrix, self).value()
        return pymel.core.datatypes.Matrix(v)

    @staticmethod
    def default():
        return pymel.core.datatypes.Matrix()

    @classmethod
    def compose(cls, translate=(0, 0, 0), rotate=(0, 0, 0), scale=(1, 1, 1), shear=(0, 0, 0)):
        nodex.utils.ensurePluginsLoaded(cls._plugins)
        composeNode = pymel.core.createNode("composeMatrix")

        if translate != (0, 0, 0):
            Nodex(translate).connect(composeNode.attr('inputTranslate'))
        if rotate != (0, 0, 0):
            Nodex(rotate).connect(composeNode.attr('inputRotate'))
        if scale != (1, 1, 1):
            Nodex(scale).connect(composeNode.attr('inputScale'))
        if shear != (0, 0, 0):
            Nodex(shear).connect(composeNode.attr('inputShear'))

        return Nodex(composeNode.attr('outputMatrix'))

    def decompose(self, translate=None, rotate=None, scale=None, shear=None, quat=None, chainAttr="outputTranslate"):
        """ Decomposes a Matrix into its translate, rotate (euler and quat), scale, shear values.

        :rtype: :class:`nodex.datatypes.Vector`
        """
        nodex.utils.ensurePluginsLoaded(self._plugins)
        decomposeNode = pymel.core.createNode("decomposeMatrix")

        self.connect(decomposeNode.attr("inputMatrix"))

        if translate is not None:
            Nodex(decomposeNode.attr("outputTranslate")).connect(translate)
        if rotate is not None:
            Nodex(decomposeNode.attr("outputRotate")).connect(rotate)
        if scale is not None:
            Nodex(decomposeNode.attr("outputScale")).connect(scale)
        if shear is not None:
            Nodex(decomposeNode.attr("outputShear")).connect(shear)
        if quat is not None:
            Nodex(decomposeNode.attr("outputQuat")).connect(quat)

        # Assume chain output based on chainAttr
        return Nodex(decomposeNode.attr(chainAttr))

    def passMatrix(self, scale=None):
        """ Multiply a matrix by a constant without caching anything

        .. note:: 'pass' shadows a built-in of Python, therefore this method is named 'passMatrix'

        :param scale: Scale factor on input matrix
        :return: The 'outMatrix' attribute as Nodex
        :rtype: :class:`nodex.datatypes.Matrix`
        """
        # no plug-in required (tested maya 2015)
        # nodex.utils.ensurePluginsLoaded(self._plugins)

        n = pymel.core.createNode("passMatrix")
        self.connect(n.attr("inMatrix"))

        if scale is not None:
            Nodex(scale).connect(n.attr("inScale"))

        return Nodex(n.attr("outMatrix"))

    def inverse(self):
        """ Returns the Nodex for the outputMatrix attribute for the inverse of this Matrix

            Uses the `inverseMatrix` node from the `matrixNodes` plug-in in Maya.

            :rtype: :class:`nodex.datatypes.Matrix`
        """
        nodex.utils.ensurePluginsLoaded(self._plugins)
        n = pymel.core.createNode("inverseMatrix")
        self.connect(n.attr("inputMatrix"))
        return Nodex(n.attr("outputMatrix"))

    def transpose(self):
        """ Returns the Nodex for the outputMatrix attribute for the transpose of this Matrix

            Uses the `transposeMatrix` node from the `matrixNodes` plug-in in Maya.

            :rtype: :class:`nodex.datatypes.Matrix`
        """
        nodex.utils.ensurePluginsLoaded(self._plugins)
        n = pymel.core.createNode("transposeMatrix")
        self.connect(n.attr("inputMatrix"))
        return Nodex(n.attr("outputMatrix"))

    def hold(self):
        """ Cache a matrix.

            Uses the `holdMatrix` node built-in from Maya.

            :rtype: :class:`nodex.datatypes.Matrix`
        """
        n = pymel.core.createNode("holdMatrix")
        self.connect(n.attr("inMatrix"))
        return Nodex(n.attr("outMatrix"))

    def multiply(self, *args):
        """ Returns the Nodex for the sumMatrix attribute for this matrix multiplied with the other arguments

            Uses the `multMatrix` node from the `matrixNodes` plug-in in Maya.

            :type *args: :class:`nodex.datatypes.Matrix`
            :rtype: :class:`nodex.datatypes.Matrix`
        """
        nodex.utils.ensurePluginsLoaded(self._plugins)

        # ensure arguments are Nodex
        args = tuple(Nodex(x) if not isinstance(x, Nodex) else x for x in args)

        # ensure all Nodex are Matrix
        for x in args:
            if not isinstance(x, Matrix):
                raise TypeError("Provided arguments must be of type 'nodex.datatypes.Matrix', "
                                "instead got {0}".format(x))

        n = pymel.core.createNode("multMatrix")

        self.connect(n.attr("matrixIn[0]"))
        for i, other_input_arg in enumerate(args):
            other_input_arg.connect(n.attr("matrixIn[{0}]".format(i+1)))

        return Nodex(n.attr("matrixSum"))

    def __mul__(self, other):
        """ Returns this matrix multiplied with another.

        .. note:: This overrides the inherited behaviour from `Array` of multiplying all individual components with
                  Matrix multiplication.

        """
        return self.multiply(other)


# TODO: Implement quaternion
# class Quaternion(Array):
#     """
#         Some methods on the `Quaternion` datatype will try to quietly load the `matrixNodes` plug-in built-in with
#         Maya to ensure the required nodes are available.
#     """
#     _plugins = ["quatNodes"]
#     _allowed_iterables = (tuple, list)
#
#     _priority = 90
#
#     @staticmethod
#     def validateAttr(attr):
#         if attr.isArray() or attr.isCompound():
#             if nodex.utils.attrDimensions(attr) == 4:
#                 return True
#         return False
#
#
#     @staticmethod
#     def isValidData(data):
#
#         if isinstance(data, pymel.core.Attribute):
#             return Quaternion.validateAttr(data)
#         elif isinstance(data, basestring):
#             try:
#                 attr = pymel.core.Attribute(data)
#                 return Quaternion.validateAttr(attr)
#             except RuntimeError:
#                 return False
#
#         if isinstance(data, Quaternion._allowed_iterables) and len(data) == 4:
#             return True
#
#     def convertData(self, data):
#
#         # attribute
#         if isinstance(data, pymel.core.Attribute):
#             return data
#         elif isinstance(data, basestring):
#             return pymel.core.Attribute(data)
#
#         # handle like Array
#         return super(Quaternion, self).convertData(data)
#
#     @staticmethod
#     def fromEuler(rotate=None, rotateOrder=None):
#         """
#             Uses `eulerToQuat` node
#
#         :param rotate: :class:`nodex.datatypes.Vector`
#         :param rotateOrder: :class:`nodex.datatypes.Int` (enum)
#         :return: :class:`nodex.datatypes.Quaternion`
#         """
#         raise NotImplementedError()
#
#     def toEuler(self):
#         raise NotImplementedError()
#
#     def inverse(self):
#         raise NotImplementedError()
#
#     def negate(self):
#         raise NotImplementedError()
#
#     def normalize(self):
#         raise NotImplementedError()
#
#     def add(self, other):
#         raise NotImplementedError()
#
#     def sub(self, other):
#         raise NotImplementedError()
#
#     def product(self, other):
#         raise NotImplementedError()
#
#     def slerp(self, other, blender=None):
#         """
#             There doesn't seem to be a slerp node in Maya so we'll need to implement it with a set of nodes.
#             Maybe: http://download.autodesk.com/us/maya/2011help/Nodes/animBlendNodeAdditiveRotation.html
#
#
#         :param other:
#         :param blender:
#         :return:
#         """
#         raise NotImplementedError()

