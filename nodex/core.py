# standard library
import itertools
from functools import partial
import logging
import abc
logger = logging.getLogger(__name__)

VERBOSE = True

# maya library
import maya.cmds as mc
import pymel.core

# local library
import nodex.utils


def connectOrSet(attr, v):
    """
        Connect or set the attribute.
    """
    if not isinstance(attr, pymel.core.Attribute):
        attr = pymel.core.Attribute(attr)

    if not isinstance(v, Nodex):
        v = Nodex(v)

    if v.isAttribute():
        pymel.core.connectAttr(v.attr(), attr, force=True)
    else:
        attr.set(v.value())
        
        
def connectOrSetVector(n, attr, input, suffices=("X", "Y", "Z")):
    if isinstance(input, (list, tuple)):
        for suffix, v in itertools.izip(suffices, input):
            connectOrSet(n.attr("{0}{1}".format(attr, suffix)), v)
    else:
        try:
            connectOrSet(n.attr("{0}".format(attr)), input)
        except (RuntimeError, pymel.core.MayaAttributeError):
            connectOrSet(n.attr("{0}{1}".format(attr, suffices[0])), input)
        
        
def connectOutputVector(n, attr, output, suffices=("X", "Y", "Z")):
    if isinstance(output, (list, tuple)):
        for suffix, v in itertools.izip(suffices, output):
            pymel.core.connectAttr(n.attr("{0}{1}".format(attr, suffix), v, force=True))
    else:
        outputAttr = pymel.core.Attribute(output)
        if outputAttr.isCompound() or outputAttr.isArray():
            try:
                pymel.core.connectAttr(n.attr(attr), outputAttr, force=True)
            except RuntimeError:
                pymel.core.connectAttr(n.attr("{0}{1}".format(attr, suffices[0])), outputAttr, force=True)
        else:
            pymel.core.connectAttr(n.attr("{0}{1}".format(attr, suffices[0])), outputAttr, force=True)


def getHighestDimensions(defaultValue, *args):
    """
        Returns the highest dimensions from multiple Nodex or return the defaultValue if it is higher than any
        of the given dimensions from the set of Nodex.
    """
    dimensions = None
    for nodex in args:
        if nodex:
            nodexDimensions = Nodex(nodex).dimensions()
            if dimensions is None or nodexDimensions > dimensions:
                dimensions = nodexDimensions

    if dimensions is None:
        dimensions = defaultValue
        
    return dimensions


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
            logger.debug("Checking data against {0}".format(cls.__name__))
        if cls.isValidData(data):
            if VERBOSE:
                logger.debug("Matched with {0}".format(cls.__name__))
            return cls


class Nodex(object):
    # TODO: At this stage this is a non-working stub
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

        if not args and dt is not None:
            # Assume default for datatype
            # Create default value for type if no args provided, but type has been provided
            if issubclass(dt, Nodex):
                data = dt.default()
            else:
                data = dt()     # instantiate by type
        elif args:
            data = args[0]
            if len(args) > 1:
                # Assume attribute passes as two args: ( node, attr )
                # Let's use PyMel to do the possible conversion and checks for us and use the resulting Attribute
                data = pymel.core.PyNode(*args)

        if data is None:
            raise RuntimeError("No datatype for PyNodex")
        assert data is not None

        if isinstance(data, Nodex):
            return data

        newcls = None
        if cls is not Nodex:
            # A PyNodex class was explicitly required, if data was passed to init check whether it is compatible with
            # the required class. If no existing object was passed, create of the required class PyNodex with default
            # values
            if not cls.validate(data):
                raise TypeError("Given data {0} is not compatible with datatype {1}".format(data, cls.__name__))
            newcls = cls
        else:
            newcls = _getDataTypeFromData(data, dt)

        if newcls:
            self = super(Nodex, cls).__new__(newcls)
            self.setReference(data, validate=False)
            return self
        else:
            raise RuntimeError("Could not determine Nodex datatype for {0}.".format(data))

    def __init__(self, *args, **kwargs):
        self._dimensions = None
        self._data = None

    @staticmethod
    def isValidData(data):
        return False

    def asAttribute(self):
        """ Creates a node that holds the reference data's value as a constant within an Attribute and returns the
            connectable Attribute as a Nodex. """
        raise NotImplementedError()

    def setReference(self, data, validate=True):
        self._dimensions = None # remove cached dimensions
        if validate:
            if not self.isValidData(data):
                raise TypeError("Can't set data to this datatype.")
        print 'getting data', data
        print 'setting data to', self.convertData(data)
        self._data = self.convertData(data)

    @abc.abstractmethod
    def convertData(self, data):
        """
            The returned type must be something that can be validly used as a value again for convertData, plus
            should be settable to a PyMel attribute (that relates to the type)
        :param data:
        :return:
        """
        pass

    @abc.abstractmethod
    def default(self):
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

    def dimensions(self):
        return 1

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
            return self.__dimensions
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
        return isinstance(self._data, pymel.core.Attribute)

    def node(self):
        """ Returns the node for the attribute that this Nodex instance is referencing.
            If not referencing an attribute an error is raised """
        if self.isAttribute():
            return self._data.node()
        else:
            raise AttributeError("This nodex does not reference an Attribute so does not refer to a node."
                                 "Data: {0}".format(self._data))

    def clearValue(self):
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
            raise ValueError('Can\'t connect to a Nodex that does not reference an Attribute.')

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


# TODO: Implement a method that allows you to quickly merge in any of the mathematical operation on an attribute.
#       Thus basically grabbing the current outputs for an output and passing them through the newly created node.
#       Nodex("pSphere1.translateX").mergeInto() or something along those lines
# TODO: Possibly also mergeInto with a provided input/output so we can easily pass-through a graph of nodes.