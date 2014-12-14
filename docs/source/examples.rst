========
Examples
========

Matrix constraint
-----------------

Perform a matrix constraint between two objects (assuming two transform objects are selected).
For readability this example uses ``pymel``, though using that package is not a requirement for using nodex.

.. code-block:: python

    import pymel.core
    from nodex.core import Nodex

    target, src = pymel.core.ls(selection=True)
    targetMat = Nodex(target.attr("worldMatrix[0]"))
    srcParentInvMat = Nodex(src.attr("parentInverseMatrix[0]"))

    localMat = targetMat * srcParentInvMat
    localMat.decompose(translate=src.attr('translate'),
                       rotate=src.attr('rotate'),
                       scale=src.attr('scale'))
