import pymel.core as pm


# region convenience-methods rewiring attributes (staticmethods)
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