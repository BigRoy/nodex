import pymel.core as pm
import maya.cmds as mc

# region convenience methods rewiring attributes


def attrPassThrough(oldAttr, passInAttr, passOutAttr):
    """ Passes oldAttr into the passInAttr and reroutes all oldAttr's output connections
        to the passOutAttr attribute. Basically rewiring and adding (passInput >--> passOutput)
        the middle.
    """
    oldAttr.connect(passInAttr, force=True)

    for out in oldAttr.outputs(plugs=True):
        oldAttr.disconnect(out)
        passOutAttr.connect(out)


def attrReplaceOutputs(oldAttr, newAttr):
    """ Replaces all outputs from `oldOutput` as new outputs coming from `newOutput` """
    for out in oldAttr.outputs(plugs=True):
        oldAttr.disconnect(out)
        newAttr.connect(out)


def attrReplaceInput(oldAttr, newAttr):
    """ Replaces all inputs going into `oldInput` towards the new input `newInput` """
    for input in oldAttr.inputs(plugs=True):
        input.disconnect(oldAttr)
        input.connect(newAttr)


def attrDimensions(attr):
    if attr.isArray():
        return attr.numElements()
    elif attr.isCompound():
        return attr.numChildren()
    else:
        return 1

# endregion


# region nodes
def plusMinusAverage(*args, **kwargs):
    from nodex.core import Nodex
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


def multiplyDivide(input1=None, input2=None, output=None, **kwargs):
    from nodex.core import Nodex

    # Ensure nodex inputs
    if input1 is not None and not isinstance(input1, Nodex):
        input1 = Nodex(input1)
    if input2 is not None and not isinstance(input2, Nodex):
        input2 = Nodex(input2)

    o = kwargs.pop("operation", 1)
    name = kwargs.pop("name", "multiplyDivide")

    n = pm.createNode("multiplyDivide", name=name)
    n.operation.set(o)  # multiply, divide, pow, etc.

    d = kwargs.pop("dimensions", None)

    # Get dimensions from input Nodex
    if d is None:
        d = max(x.dimensions() for x in [input1, input2, output] if not x is None)

    if d > 3:
        raise RuntimeError("Can't use plusMinusAverage with higher dimensions than 3")

    # Attrs for dimensions
    input1Attrs = {1: "input1X", 2: ["input1X", "input1Y"], 3: "input1"}
    input1Attr = input1Attrs[d]
    input2Attrs = {1: "input2X", 2: ["input2X", "input2Y"], 3: "input2"}
    input2Attr = input2Attrs[d]
    outputAttrs = {1: "outputX", 2: ["outputX", "outputY"], 3: "output"}
    outputAttr = outputAttrs[d]

    for attr, inputValue in [(input1Attr, input1),
                             (input2Attr, input2)]:
        if inputValue is not None:
            inputValue.connect(n.attr(attr))

    if output is not None:
        Nodex(n.attr(outputAttr)).connect(output)

    return Nodex(n.attr(outputAttr))


def clamp(input=None, min=None, max=None, output=None, **kwargs):
    # TODO: Revise utils.clamp to work with the new Nodex class

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


def doubleLinear(input1=None, input2=None, output=None, nodeType="multDoubleLinear", **kwargs):
    from nodex.core import Nodex

    name = kwargs.pop("name", "clamp")
    n = pm.createNode(nodeType, name=name)

    if input1 is not None:
        Nodex(input1).connect(n.attr('input1'))

    if input2 is not None:
        Nodex(input2).connect(n.attr('input2'))

    if output is not None:
        Nodex(n.attr('output')).connect(output)

    return Nodex(n.attr("output"))


def condition(firstTerm=None, secondTerm=None, ifTrue=None, ifFalse=None, output=None, **kwargs):
    from nodex.core import Nodex
    o = kwargs.pop("operation", 0)
    name = kwargs.pop("name", "condition")
    d = kwargs.pop("dimensions", None)
    output = kwargs.pop("output", None)

    # Ensure inputs are Nodex
    if firstTerm is not None and not isinstance(firstTerm, Nodex):
        firstTerm = Nodex(firstTerm)
    if secondTerm is not None and not isinstance(secondTerm, Nodex):
        secondTerm = Nodex(secondTerm)
    if ifTrue is not None and not isinstance(ifTrue, Nodex):
        ifTrue = Nodex(ifTrue)
    if ifFalse is not None and not isinstance(ifFalse, Nodex):
        ifFalse = Nodex(ifFalse)

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
        firstTerm.connect(n.attr("firstTerm"))

    if secondTerm is not None:
        secondTerm.connect(n.attr("secondTerm"))

    if ifTrue is not None:
        ifTrue.connect(n.attr("colorIfTrue"))
    else:
        n.attr("colorIfTrue").set((1, 1, 1))

    if ifFalse is not None:
        ifFalse.connect(n.attr("colorIfFalse"))
    else:
        n.attr("colorIfFalse").set((0, 0, 0))

    if output is not None:
        ifFalse.connect(outputAttr)

    return Nodex(outputAttr)

# endregion


def ensurePluginsLoaded(plugins):
    for p in plugins:
        mc.loadPlugin(p, quiet=True)