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
    try:
        inputAttr = pm.Attribute(v)
        pm.connectAttr(inputAttr, attr, force=True)
    except (pm.MayaAttributeError, pm.MayaNodeError):
        attr.set(v)
       
        
def connectOutput(attr, v):
    pm.connectAttr(n.attr(attr), output, force=True)
        
        
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
            # TODO: Test if array Nodex performs as supposed to.
            # 1. validate every element has 'max' single dimension of depth
            # 2. convert any references internal to the array
            v = tuple(self.__convertReference(x) for x in v)
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
        try:
            return pm.Attribute(self.v).get()
        except (pm.MayaNodeError, RuntimeError):
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
            return self.__reference
        else:
            raise AttributeError("This nodex does not reference an Attribute so does not refer to a node."
                                 "Reference: {0}".format(self.__reference))
        
    def connectTo(self, other, force=True):
        """ Connects this Nodex attribute to the `other` object.
        
            self (source) ---> other (destination)
        """
        # TODO: Implement automatic conversion of input-output types (vector/arrays/etc.)
        if not isinstance(other, Nodex):
            other = Nodex(other)
        pm.connectAttr(self.attr(), other.attr(), force=force)
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
        d = kwargs.pop("dimensions", 1)
        o = kwargs.pop("operation", 1)
        name = kwargs.pop("name", "plusMinusAverage")
        output = kwargs.pop("output", None)
        
        # TODO: If dimension (d) is None, then it should automatically retrieve the biggest dimension from input values (up to 3)
        #       and use that.
        
        n = pm.createNode("plusMinusAverage", name=name)
        n.operation.set(o) # average
        for i, v in enumerate(args):
            connectOrSet(n.attr("input{dimension}D[{index}]".format(dimension=d, index=i)), v)
            
        if output is not None:
            connectOutput(n.attr("output"), v)
            
        return Nodex(n.attr('output'))
    
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
            connectOutput(n.attr("output"), output)
        
        return Nodex(n.attr("output"))
        
    # Condition
    @staticmethod      
    def _condition(firstTerm=None, secondTerm=None, ifTrue=None, ifFalse=None, output=None, **kwargs):
        o = kwargs.pop("operation", 1)
        name = kwargs.pop("name", "clamp")
        #output = kwargs.pop("output", None)
        
        suffices = ["R", "G", "B"]
        
        n = pm.createNode("condition", name=name)
        n.operation.set(o)
        
        if firstTerm is not None:
            connectOrSet(n.attr("firstTerm"), firstTerm)
        
        if secondTerm is not None:
            connectOrSet(n.attr("secondTerm"), secondTerm)
        
        if ifTrue is not None:
            connectOrSetVector(n, "colorIfTrue", ifTrue, suffices=suffices)
        
        if ifFalse is not None:
            connectOrSetVector(n, "colorIfFalse", ifFalse, suffices=suffices)
            
        if output is not None:
            connectOutputVector(n, "outColor", output, suffices=suffices)
            
        return Nodex(n.attr("outColor"))
    # endregion

    def __calc(self, other, func):
        """ Convenience method for the special methods like __add__, __sub__, etc. """
        other = other.v if isinstance(other, Nodex) else other
        return func(self, other)

    # region special methods override: mathematical operators
    def __add__(self, other):
        return self.__calc(other, func=Nodex.sum1D)
        
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
        return self.v
        
    def __repr__(self):
        return "Nodex({0})".format(self.v)
                
# Static methods
# These static methods return PyMel nodes that are created for that operation.
# Though if the keyword argument `returnType` is provided it can be adjusted to either:
#     0. Create node `pymel.PyNode()`
#     1. Output attribute as `Nodex()`
#     2. Output attribute as `pymel.Attribute()`
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
#Nodex("pSphere1.translateX").mergeInto() or something along those lines
# TODO: Possibly also mergeInto with a provided input/output so we can easily pass-through a graph of nodes.