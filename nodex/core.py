# standard library
import itertools
from functools import partial
import logging
import abc
logger = logging.getLogger(__name__)

# maya library
import maya.cmds as mc
import pymel.core

# local library
import nodex.utils

VERBOSE = False


def find_subclasses(module, clazz):
    import inspect
    return [cls for name, cls in inspect.getmembers(module) if cls != clazz and
                                                               inspect.isclass(cls) and
                                                               issubclass(cls, clazz)]


def _getDataTypeFromData(data, datatype=None):
    if datatype is not None:
        if not issubclass(datatype, Nodex):
            raise TypeError("Preferred datatype should be of type PyNodex")

        if datatype.isValidData(data):
            return datatype

    import inspect
    import datatypes
    klasses = find_subclasses(datatypes, Nodex)

    for cls in sorted(klasses, key=lambda x: x.priority()):
        if VERBOSE:
            logger.debug("Checking data {0} against {1}".format(data, cls.__name__))
        if cls.isValidData(data):
            if VERBOSE:
                logger.debug("Matched data {0} with {0}".format(data, cls.__name__))
            return cls


class UndefinedNodexError(RuntimeError):
    pass


class Nodex(object):
    """
    Abstract class that is base for all Nodex datatype classes.

    The names of nodes and attributes can be passed to this class, and the appropriate subclass will be determined.
    Also you can pass in a value based on certain datatypes to allow for automatic conversion (eg. Matrices)
    The conversion are based on definitions defined in `nodex.datatypes`

        >>> Nodex('persp.tx')
        dt.Float(u'persp.translateX')

    If the value can't be converted to a valid data type an error will be raised.

    (For now loosely based on the implementation of PyNode in pymel)
    """
    _priority = -100

    @classmethod
    def priority(cls):
        return cls._priority

    def __new__(cls, *args, **kwargs):
        """ Catch all creation for PyNodex classes, creates correct class depending on type passed. """
        import datatypes

        data = None
        dt = kwargs.get("type", None)

        if not args:
            # Assume default for datatype
            # Create default value for type if no args provided, but type has been provided
            if issubclass(cls, Nodex):
                data = cls.default()
            elif dt is not None:
                data = dt()     # instantiate by type
        else:
            data = args[0]
            if len(args) > 1:
                # Assume attribute passes as two args: ( node, attr )
                # Let's use PyMel to do the possible conversion and checks for us and use the resulting Attribute
                data = pymel.core.PyNode(*args)

        if data is None:
            raise TypeError("No valid datatype for Nodex. Data {0}".format(data))
        assert data is not None

        if isinstance(data, Nodex):
            return data

        # We shouldn't make this assumption here, plus it breaks a lot of stuff. :)
        #if isinstance(data, (list, tuple)) and len(data) == 1:
        #    data = data[0]

        newcls = None
        if cls is not Nodex:
            # A PyNodex class was explicitly required, if data was passed to init check whether it is compatible with
            # the required class. If no existing object was passed, create of the required class PyNodex with default
            # values
            if not cls.isValidData(data):
                raise TypeError("Given data {0} is not compatible with datatype {1}".format(data, cls.__name__))
            newcls = cls
        else:
            newcls = _getDataTypeFromData(data, dt)

        if newcls:
            self = super(Nodex, cls).__new__(newcls)
            self.setReference(data, validate=False)
            return self
        else:
            raise UndefinedNodexError("Could not determine Nodex datatype for {0}.".format(data))

    @staticmethod
    def isValidData(data):
        return False

    def asAttribute(self):
        """ Creates a node that holds the reference data's value as a constant within an Attribute and returns the
            connectable Attribute as a Nodex. """
        raise NotImplementedError()

    def setReference(self, data, validate=True):
        self._dimensions = None     # remove cached dimensions
        if validate:
            if not self.isValidData(data):
                raise TypeError("Can't set data to this datatype.")
        self._data = self.convertData(data)

    @abc.abstractmethod
    def convertData(self, data):
        """
            The returned type must be something that can be validly used as a value again for convertData, plus
            should be settable to a PyMel attribute (that relates to the type)
        """
        pass

    @staticmethod
    def default():
        """
        :return: Default value for this datatype. The returned type must be something that can be validly converted by
                 this datatype in 'self.convertData'
        """
        return None

    def value(self):
        if self.isAttribute():
            return self.v.get()
        elif isinstance(self.v, tuple):
            return tuple(x.value() for x in self.v)
        else:
            return self.v

    # region nodex value-reference methods
    @property
    def v(self):
        """ Short convenience property to get to the Nodex's referenced content """
        return self._data

    def data(self):
        return self._data

    def value(self):
        if self.isAttribute():
            return self.v.get()
        elif isinstance(self.v, tuple):
            return tuple(x.value() for x in self.v)
        else:
            return self.v
    # endregion

    # region nodex combined methods (whilst referencing: attribute || single numeric || array)
    def dimensions(self):
        if self._dimensions is not None:
            return self._dimensions

        if self.isAttribute():
            self._dimensions = nodex.utils.attrDimensions(self.attr())
            return self._dimensions
        elif self.isSingleNumeric():
            return 1
        else:
            return len(self._data)

    def isSingleNumeric(self):
        if self.isAttribute():
            return nodex.utils.attrDimensions(self.attr()) == 1
        else:
            return isinstance(self._data, (int, float))
    # endregion

    # region nodex attribute methods
    def attr(self):
        """ Returns the attribute this Nodex instance is referencing.
            If not referencing an attribute an error is raised """
        if self.isAttribute():
            return self._data
        else:
            return None

    def isAttribute(self):
        """ Returns True if this Nodex instance references a valid attribute, else False. """
        #if isinstance(self._data, (tuple)) and all(isinstance(x, pymel.core.Attribute) for x in self._data):
        #    return True
        if isinstance(self._data, pymel.core.Attribute):
            return True

        return False

    def node(self):
        """ Returns the node for the attribute that this Nodex instance is referencing.
            If not referencing an attribute an error is raised """
        if self.isAttribute():
            return self._data.node()
        else:
            raise AttributeError("This nodex does not reference an Attribute so does not refer to a node."
                                 "Data: {0}".format(self._data))
    # endregion

    def clearValue(self):
        """ Set the default value for this Nodex instance (reset value) """
        self.connect(Nodex(self.default()))

    def connect(self, other, allowGrow=False):
        """
            Connects one Nodex attribute/value to another attribute.
            This method ensures to perform a connection even if the dimensions between the Nodex attributes differs.

            self (source) ---> other (destination)

            :param other: The destination Nodex to connect to.
            :type other: Nodex

            :return: The resulting dimensions
        """
        if not isinstance(other, Nodex):
            other = Nodex(other)

        dim = self.dimensions()
        otherDim = other.dimensions()

        if not other.isAttribute():
            raise ValueError('Can\'t connect to a Nodex that does not reference an Attribute. '
                             'Other is: {0}'.format(other))

        if dim == otherDim:
            if self.isAttribute():
                self.attr().connect(other.attr()) # connect pymel attributes
            else:
                other.attr().set(self.value())  # assign referenced value
            return dim
        elif dim == 1 and allowGrow:   # --> otherDim != 1 and otherDim > 1
            for i in range(otherDim):
                self.connect(other[i])
                logger.warning('Connected single attribute {0} to larger attribute {1}.'
                               'Attribute connected to all inputs of larger attribute'.format(
                               self, other))
            return otherDim
        elif otherDim < dim:
            self[:otherDim].connect(other)
            logger.warning('Truncated attribute {0} to connect to smaller attribute {1}.'.format(
                            self, other))
            return otherDim
        elif otherDim > dim:
            resultDim = self.connect(other[:dim])  # connect to truncated length of other
            other[dim+1:].clearValue()   # clear remaining values
            logger.warning('Connected smaller attibute {0} to larger attibute {0}.'
                           'The resulting plug is larger and remaining values are cleared (set to 0).'.format(
                           self, other))
            return resultDim
    # endregion

    def __str__(self):
        return "{0}({1})".format(self.__class__.__name__, self.v)

    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__, self.v)

    def __getitem__(self, item):
        # TODO: Implement tests for __getitem__
        # TODO: Implement proper __getitem__
        if self.isAttribute():
            attr = self.attr()
            if attr.isArray():
                if isinstance(item, int):
                    return Nodex(attr.elementByPhysicalIndex(item))
                elif isinstance(item, slice):
                    return Nodex([attr.elementByPhysicalIndex(i) for i in xrange(item.start, item.stop, item.step)])
            elif attr.isCompound():
                return Nodex(attr.children()[item])

        if isinstance(item, slice):
            return Nodex(self.v[item])
        elif isinstance(item, int):
            return Nodex(self.v[item])


# TODO: Implement a method that allows you to quickly merge in any of the mathematical operation on an attribute.
#       Thus basically grabbing the current outputs for an output and passing them through the newly created node.
#       Nodex("pSphere1.translateX").mergeInto() or something along those lines
# TODO: Possibly also mergeInto with a provided input/output so we can easily pass-through a graph of nodes.


class Math(object):
    @staticmethod
    def bimath(self, other, func):
        """ Convenience method for the special methods like __add__, __sub__, etc. """
        if not isinstance(other, Nodex):
            other = Nodex(other)

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
#Math.blend (=blendColors)
#Math.setRange
#Math.contrast
#Math.reverse
#Math.stencil
#Math.overlay (= multiple nodes)
#Math.vectorProduct
#Math.angleBetween
#Math.unitConversion