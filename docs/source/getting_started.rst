===============
Getting Started
===============


Hello world!
------------

Let's get your feet wet in the world of Nodex. First we import the Nodex class from the package (for convenience).

.. code-block:: python

    from nodex.core import Nodex

Ensure you have a fresh scene and create two spheres, they should be called `pSphere1` and `pSphere2`.
We'll position pSphere2 towards pSphere1 with a maximum distance of 5 (from the origin) which will result in a spherical
position.

So first we need to get the translate of pSphere1

.. code-block:: python

    nodex = Nodex('pSphere1.translate')

# TODO: Write the rest

Complete code snippet:

.. code-block:: python

    from nodex.core import Nodex

    # free position
    target = Nodex('pSphere1.translate')

    # limited position (5.0 units from origin)
    targetMax = target.normal() * 5.0

    # add a condition (so we use the limited targetMax position if the target is further away than 5.0 units)
    distanceFromOrigin = target.length()
    conditionOutput = Math.greaterThan(distanceFromOrigin, 5.0, ifTrue=targetMax, ifFalse=target)

    conditionOutput.connect('pSphere2.translate')
