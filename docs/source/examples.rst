========
Examples
========

Check if all True
-----------------

Check if x, y, z are all the same value

.. code-block:: python

    from nodex.core import Nodex

    xy = (Nodex("pSphere1.tx") == Nodex("pSphere1.ty"))
    yz = (Nodex("pSphere1.ty") == Nodex("pSphere1.tz"))
    xz = (Nodex("pSphere1.tx") == Nodex("pSphere1.tz"))
    sum = Math.sum(xy, yz, xz) # sum in a single node
    cond_all = (sum == 3)

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


Conditional Calculation
-----------------------

A conditional calculation can be useful for rigs. For example one might want to enable/disable the stretchiness of the
IK. Assuming we have an object called `CTRL` with a Boolean attribute `stretchy` we could write something like

.. code-block:: python

    from nodex.core import Nodex, Math

    originalLength = Nodex(5.0) # just a random constant for now
    newLength = Nodex('armStartPoint.translate').distanceTo('armEndPoint.translate') # calculate new required length
    resultLength = Math.equal('CTRL.stretchy', True, ifTrue=newLength, ifFalse=originalLength)

Or if you would like to blend and the stretchy value is a float value between 0.0 and 1.0.

.. code-block:: python

    from nodex.core import Nodex, Math

    originalLength = Nodex(5.0) # just a random constant for now
    newLength = Nodex('armStartPoint.translate').distanceTo('armEndPoint.translate') # calculate new required length
    resultLength = Math.blend(originalLength, newLength, blender="CTRL.stretchy")


Using mathematical operators
----------------------------

Using Nodex you can write complex expressions in a readable way.

.. code-block:: python

    from nodex.core import Nodex, Math
    import math

    pi = Nodex(math.pi)
    multiplier = Nodex('ctrl.multiplier')
    x = Nodex('ctrl.x')
    y = Nodex('ctrl.y')

    # some random expressions
    result = (x * multiplier) + (y * (1.0 - multiplier)) * pi / 2.0
    result2 = Math.sqrt((x^2) + (y^2))
    result3 = result * result2 - (1.0-result).abs()

Getting the length of a vector using algebra.

.. code-block:: python

    from nodex.core import Nodex, Math

    v = Nodex([1, 0, 0])
    v_squared_components = v ^ 2.0
    v_length = Math.sum(v[0], v[1], v[2])

Or because a Nodex of three dimensions automatically instantiates as a :class:`nodex.datatypes.Vector` we can directly
perform that calculation using one of its methods.

.. code-block:: python

    v = Nodex([1, 0, 0])
    v_length = v.length()