# standard library
import itertools
from functools import partial
import logging
logger = logging.getLogger(__name__)

# maya library
import maya.cmds as mc
import pymel.core as pm

# local library
import nodex.utils


def connectOrSet(attr, v):
    """
        Connect or set the attribute.
    """
    if not isinstance(attr, pm.Attribute):
        attr = pm.Attribute(attr)

    if not isinstance(v, Nodex):
        v = Nodex(v)

    if v.isAttribute():
        pm.connectAttr(v.attr(), attr, force=True)
    else:
        attr.set(v.value())
        
        
def connectOrSetVector(n, attr, input, suffices=("X", "Y", "Z")):
    if isinstance(input, (list, tuple)):
        for suffix, v in itertools.izip(suffices, input):
            connectOrSet(n.attr("{0}{1}".format(attr, suffix)), v)
    else:
        try:
            connectOrSet(n.attr("{0}".format(attr)), input)
        except (RuntimeError, pm.MayaAttributeError):
            connectOrSet(n.attr("{0}{1}".format(attr, suffices[0])), input)
        
        
def connectOutputVector(n, attr, output, suffices=("X", "Y", "Z")):
    if isinstance(output, (list, tuple)):
        for suffix, v in itertools.izip(suffices, output):
            pm.connectAttr(n.attr("{0}{1}".format(attr, suffix), v, force=True))
    else:
        outputAttr = pm.Attribute(output)
        if outputAttr.isCompound() or outputAttr.isArray():
            try:
                pm.connectAttr(n.attr(attr), outputAttr, force=True)
            except RuntimeError:
                pm.connectAttr(n.attr("{0}{1}".format(attr, suffices[0])), outputAttr, force=True)
        else:
            pm.connectAttr(n.attr("{0}{1}".format(attr, suffices[0])), outputAttr, force=True)


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


class PyNodex(object):
    # TODO: At this stage this is a non-working stub
    """
    Abstract class that is base for all Nodex datatype classes.

    The names of nodes and attributes can be passed to this class, and the appropriate subclass will be determined.
    Also you can pass in a value based on certain datatypes to allow for automatic conversion (eg. Matrices)
    The conversion are based on definitions defined in `nodex.datatypes`

        >>> PyNodex('persp.tx')
        dt.Float(u'persp.translateX')

    If the value can't be converted to a valid data type an error will be raised.

    (For now loosely based on the implementation of PyNode in pymel)
    """
    def __new__(cls, *args, **kwargs):
        """ Catch all creation for PyNodex classes, creates correct class depending on type passed. """
        import datatypes

        dt = kwargs.get("type", None)

        if not args and dt is not None:
            # Assume default for datatype
            # Create default value for type if no args provided, but type has been provided
            if isinstance(dt, datatypes.DataTypeBase):
                data = dt.default()
            else:
                data = dt()     # instantiate by type
        elif args:
            data = args[0]
            if len(args) > 1:
                # Assume attribute passes as two args: ( node, attr )
                # Let's use PyMel to do the possible conversion and checks for us and use the resulting Attribute
                data = pm.PyNode(*args)

        if data is None:
            raise RuntimeError("No datatype for PyNodex")
        assert data is not None

        if isinstance(data, PyNodex):
            return data

        if cls is not PyNodex:
            # A PyNodex class was explicitly required, if data was passed to init check whether it is compatible with
            # the required class. If no existing object was passed, create of the required class PyNodex with default
            # values
            if not cls.validate(data):
                raise TypeError("Given data {0} is not compatible with datatype {1}".format(data, cls.__name__))
            raise NotImplementedError("TODO")
        else:
            newcls = datatypes._getType(data)

        if newcls:
            self = super(PyNodex, cls).__new__(newcls)
            self.setReference(data) # not sure if this is supposed to be in here
            return self


class Nodex(object):
    """
        The base Nodex class that contains the functionality for the Maya Expressions.

        A nodex references a certain 'value' for the expression. This can either be an Attribute or a Value object.
        Upon setting a new reference it will try to convert any input into a valid reference object.
    """
    # TODO: Override in-place mathematical operators.
    # TODO: Override right-place mathematical operators.

    def __convertReference(self, ref):
        v = ref # temp, so we don't change input

        # attribute
        if isinstance(v, pm.Attribute):
            return v
        elif isinstance(v, basestring):
            try:
                return pm.Attribute(v)
            except TypeError:
                # TODO: check if node has a known conversion if so get the default output attribute (this should be extendible)
                v = pm.PyNode(v)
                raise

        # array
        if isinstance(v, list):
            # ensure hashable and non-mutable array
            v = tuple(v)

        if isinstance(v, tuple):
            # Convert any references internal to the array
            v = tuple(Nodex(x) for x in v)
            # Validate every element has max single dimension of depth
            if any(x.dimensions() > 1 for x in v):
                raise ValueError("Can't create an Array type of Nodex that nests attributes/values with a "
                                 "higher dimension than one.")
            return v

        # single numeric
        if isinstance(v, (float, int, bool)):
            return v

        raise TypeError("Reference can't be converted, wrong type: {0} (Type is '{1}')".format(ref, type(ref)))
    
    def __init__(self, v):
        self.__dimensions = None
        self.__reference = None

        self.setReference(v)

    def setReference(self, v):
        """ Either references a pymel Attribute or a Value. """
        self.__reference = self.__convertReference(v)
        self.removeCaches() # initialize

    def removeCaches(self):
        self.__dimensions = None
        
    # region nodex value-reference methods
    @property
    def v(self):
        """ Short convenience property to get to the Nodex's referenced content """
        return self.__reference
        
    def reference(self):
        return self.__reference
        
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
        if self.__dimensions is not None:
            return self.__dimensions

        if self.isAttribute():
            self.__dimensions = nodex.utils.attrDimensions(self.attr())
            return self.__dimensions
        elif self.isSingleNumeric():
            return 1
        else:
            return len(self.__reference)

    def isSingleNumeric(self):
        if self.isAttribute():
            return nodex.utils.attrDimensions(self.attr()) == 1
        else:
            return isinstance(self.v, (int, float))
    # endregion

    # region nodex attribute methods
    def attr(self):
        """ Returns the attribute this Nodex instance is referencing.
            If not referencing an attribute an error is raised """
        if self.isAttribute():
            return self.__reference
        else:
            return None

    def isAttribute(self):        
        """ Returns True if this Nodex instance references a valid attribute, else False. """
        return isinstance(self.__reference, pm.Attribute)
        
    def node(self):
        """ Returns the node for the attribute that this Nodex instance is referencing.
            If not referencing an attribute an error is raised """
        if self.isAttribute():
            return self.__reference.node()
        else:
            raise AttributeError("This nodex does not reference an Attribute so does not refer to a node."
                                 "Reference: {0}".format(self.__reference))
        
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
            other[dim+1:].clearValue() # clear remaining values
            logger.warning('Connected smaller attibute {0} to larger attibute {0}.'
                           'The resulting plug is larger and remaining values are cleared (set to 0).'.format(
                           self, other))
            return resultDim
    # endregion
             
    # region mathematic-utility functions (staticmethods)     
    # Clamp
    @staticmethod
    def _multiplyDivide(input1=None, input2=None, output=None, **kwargs):
        o = kwargs.pop("operation", 1)
        name = kwargs.pop("name", "multiplyDivide")
        
        n = pm.createNode("multiplyDivide", name=name)
        n.operation.set(o) # average
        
        for attr, input in [("input1", input1), ("input2", input2)]:
            if input is not None:
                connectOrSetVector(n, attr, input)
            
        
        if output is not None:
            connectOutputVector(n, "output", output)
                
        dimensions = getHighestDimensions(3, input1, input2)
        if dimensions > 1:
            pass
            
        return Nodex(n.attr('output'))
        
    # Plus-Minus average
    @staticmethod      
    def _plusMinusAverage(*args, **kwargs):
        d = kwargs.pop("dimensions", None)
        o = kwargs.pop("operation", 1)
        name = kwargs.pop("name", "plusMinusAverage")
        output = kwargs.pop("output3D", None)

        # Get dimensions from input Nodex
        if d is None:
            d = max(x.dimensions() for x in args)

        if d > 3:
            raise RuntimeError("Can't use plusMinusAverage with higher dimensions than 3")

        # Get corresponding output attribute/length for the current dimension
        resultAttrs = {1: "output1D", 2: "output2D", 3: "output3D"}
        resultAttr = resultAttrs[d]
        
        n = pm.createNode("plusMinusAverage", name=name)
        n.operation.set(o) # average
        for i, v in enumerate(args):
            n_input_attr = n.attr("input{dimension}D[{index}]".format(dimension=d, index=i))
            v.connect(n_input_attr)

        result = Nodex(n.attr(resultAttr))
        if output is not None:
            result.connect(output)
            
        return result
    
    # Clamp
    @staticmethod      
    def _clamp(input=None, min=None, max=None, output=None, **kwargs):
        name = kwargs.pop("name", "clamp")
        suffices = ["R", "G", "B"]
        
        n = pm.createNode("clamp", name=name)
        
        if input is not None:
            connectOrSetVector(n, "input", input, suffices=suffices)
        
        if min is not None:
            connectOrSetVector(n, "min", min, suffices=suffices)
        
        if max is not None:
            connectOrSetVector(n, "max", max, suffices=suffices)
            
        if output is not None:
            connectOutputVector(n, "output", output, suffices=suffices)
            
        return Nodex(n.attr('output'))
        
    # Double Linear (for multDoubleLinear and addDoubleLinear)
    @staticmethod
    def _doubleLinear(input1=None, input2=None, output=None, nodeType="multDoubleLinear", **kwargs):
        
        name = kwargs.pop("name", "clamp")
        n = pm.createNode(nodeType, name=name)
        
        if input1 is not None:
            connectOrSet(n.attr("input1"), input1)
        
        if input2 is not None:
            connectOrSet(n.attr("input2"), input2)
            
        if output is not None:
            pass
            #connectOutput(n.attr("output"), output)
        
        return Nodex(n.attr("output"))
        
    # Condition
    @staticmethod      
    def _condition(firstTerm=None, secondTerm=None, ifTrue=None, ifFalse=None, output=None, **kwargs):
        o = kwargs.pop("operation", 0)
        name = kwargs.pop("name", "condition")
        d = kwargs.pop("dimensions", None)
        output = kwargs.pop("output", None)

        # Get dimensions from input Nodex
        if d is None:
            d = max(x.dimensions() for x in [firstTerm, secondTerm, ifTrue, ifFalse] if not x is None)

        if d > 3:
            raise RuntimeError("Can't use plusMinusAverage with higher dimensions than 3")
        
        suffices = ["R", "G", "B"]
        
        n = pm.createNode("condition", name=name)
        n.operation.set(o)

        # region define output attribute
        # Get corresponding output attribute/length for the current dimension
        outputAttrs = {1: "outColorR", 2: ["outColorR", "outColorG"], 3: "outColor"}
        outputAttr = outputAttrs[d]
        # use node name plus attribute to identify output so we can use it as the nodex directly
        if isinstance(outputAttr, list):
            outputAttr = ["{0}.{1}".format(n.name(), x) for x in outputAttr]
        else:
            outputAttr = "{0}.{1}".format(n.name(), outputAttr)
        # endregion

        
        if firstTerm is not None:
            connectOrSet(n.attr("firstTerm"), firstTerm)
        
        if secondTerm is not None:
            connectOrSet(n.attr("secondTerm"), secondTerm)
        
        if ifTrue is not None:
            connectOrSetVector(n, "colorIfTrue", ifTrue, suffices=suffices)
        else:
            n.attr("colorIfTrue").set((1, 1, 1))
        
        if ifFalse is not None:
            connectOrSetVector(n, "colorIfFalse", ifFalse, suffices=suffices)
        else:
            n.attr("colorIfFalse").set((0, 0, 0))
            
        if output is not None:
            connectOrSet(Nodex(outputAttr), output)
            
        return Nodex(outputAttr)
    # endregion

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

    def __calc(self, other, func):
        """ Convenience method for the special methods like __add__, __sub__, etc. """
        if not isinstance(other, Nodex):
            other = Nodex(other)
        return func(self, other)

    # region special methods override: mathematical operators
    def __add__(self, other):
        return self.__calc(other, func=Nodex.sum)
        
    def __sub__(self, other):
        return self.__calc(other, func=Nodex.subtract)
        
    def __mul__(self, other):
        return self.__calc(other, func=Nodex.multiply)
        
    def __xor__(self, other):
        return self.__calc(other, func=Nodex.power)
        
    def __pow__(self, other):
        return self.__calc(other, func=Nodex.power)
        
    def __div__(self, other):
        return self.__calc(other, func=Nodex.divide)
    # endregion
       
       
    # region special methods override: rich-comparisons-methods 
    def __eq__(self, other):
        return self.__calc(other, func=Nodex.equal)
        
    def __ne__(self, other):
        return self.__calc(other, func=Nodex.notEqual)
        
    def __gt__(self, other):
        return self.__calc(other, func=Nodex.greaterThan)
        
    def __ge__(self, other):
        return self.__calc(other, func=Nodex.greaterOrEqual)
        
    def __lt__(self, other):
        return self.__calc(other, func=Nodex.lessThan)
        
    def __le__(self, other):
        return self.__calc(other, func=Nodex.lessOrEqual)
    # endregion    
    
    def __str__(self):
        return "Nodex({0})".format(self.v)
        
    def __repr__(self):
        return "Nodex({0})".format(self.v)
                
# Static methods
# These static methods return a new Nodex instance set to the expected output of the newly created node(s).
#     
Nodex.multiply = partial(Nodex._multiplyDivide, operation=1, name="multiply")
Nodex.multDouble = partial(Nodex._doubleLinear, nodeType="multDoubleLinear", name="multDouble")
Nodex.divide = partial(Nodex._multiplyDivide, operation=2, name="divide")
Nodex.power = partial(Nodex._multiplyDivide, operation=3, name="power")
Nodex.add = partial(Nodex._doubleLinear, nodeType="addDoubleLinear", name="add")
Nodex.sum = partial(Nodex._plusMinusAverage, dimensions=None, operation=1, name="sum") # TODO: Implement THIS!
Nodex.sum1D = partial(Nodex._plusMinusAverage, dimensions=1, operation=1, name="sum1D")
Nodex.sum2D = partial(Nodex._plusMinusAverage, dimensions=2, operation=1, name="sum2D")
Nodex.sum3D = partial(Nodex._plusMinusAverage, dimensions=3, operation=1, name="sum3D")
Nodex.subtract = partial(Nodex._plusMinusAverage, dimensions=None, operation=2, name="subtract")
Nodex.subtract1D = partial(Nodex._plusMinusAverage, dimensions=1, operation=2, name="subtract1D")
Nodex.subtract2D = partial(Nodex._plusMinusAverage, dimensions=2, operation=2, name="subtract2D")
Nodex.subtract3D = partial(Nodex._plusMinusAverage, dimensions=3, operation=2, name="subtract3D")
Nodex.average1D = partial(Nodex._plusMinusAverage, dimensions=1, operation=3, name="average1D")
Nodex.average2D = partial(Nodex._plusMinusAverage, dimensions=2, operation=3, name="average2D")
Nodex.average3D = partial(Nodex._plusMinusAverage, dimensions=3, operation=3, name="average3D")
Nodex.clamp = partial(Nodex._clamp, name="clamp")
Nodex.equal = partial(Nodex._condition, operation=0, name="condition_equal")
Nodex.notEqual = partial(Nodex._condition, operation=1, name="condition_notEqual")
Nodex.greaterThan = partial(Nodex._condition, operation=2, name="condition_greaterThan")
Nodex.greaterOrEqual = partial(Nodex._condition, operation=3, name="condition_greaterOrEqual")
Nodex.lessThan = partial(Nodex._condition, operation=4, name="condition_lessThan")
Nodex.lessOrEqual = partial(Nodex._condition, operation=5, name="condition_lessOrEqual")

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

# TODO: Implement a method that allows you to quickly merge in any of the mathematical operation on an attribute.
#       Thus basically grabbing the current outputs for an output and passing them through the newly created node.
#       Nodex("pSphere1.translateX").mergeInto() or something along those lines
# TODO: Possibly also mergeInto with a provided input/output so we can easily pass-through a graph of nodes.