import pymel.core as pm



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
    o = kwargs.pop("operation", 1)
    name = kwargs.pop("name", "multiplyDivide")

    n = pm.createNode("multiplyDivide", name=name)
    n.operation.set(o) # average

    for attr, inputValue in [("input1", input1),
                             ("input2", input2)]:
        if inputValue is not None:
            Nodex(inputValue).connect(n.attr(attr))

    if output is not None:
        Nodex(output).connect(n.attr("output"))

    #dimensions = getHighestDimensions(3, input1, input2)
    #if dimensions > 1:
    #    pass

    return Nodex(n.attr('output'))


def clamp(input=None, min=None, max=None, output=None, **kwargs):
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


def condition(firstTerm=None, secondTerm=None, ifTrue=None, ifFalse=None, output=None, **kwargs):
    from nodex.core import Nodex
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
        Nodex(firstTerm).connect(n.attr("firstTerm"))

    if secondTerm is not None:
        Nodex(secondTerm).connect(n.attr("secondTerm"))

    if ifTrue is not None:
        Nodex(ifTrue).connect(n.attr("colorIfTrue"))
    else:
        n.attr("colorIfTrue").set((1, 1, 1))

    if ifFalse is not None:
        Nodex(ifFalse).connect(n.attr("colorIfFalse"))
    else:
        n.attr("colorIfFalse").set((0, 0, 0))

    if output is not None:
        Nodex(ifFalse).connect(outputAttr)

    return Nodex(outputAttr)

# endregion