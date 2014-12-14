=====================
Introduction to Nodex
=====================

What is Nodex?
==============

**Nodex** is a *Python* package to be used with *Autodesk Maya*. It defines an object-oriented approach to creating and
designing node graphs. It's especially powerful when designing complex mathematical node graphs because of its ease of
use and readability of the resulting code.

.. code-block:: python

    from nodex.core import Nodex

    x = Nodex('locator1.translate')
    y = Nodex('locator2.translate')

    result = (0.5 * x) + (0.5 * y)
    result.connect('locator3.translate')

When to use Nodex?
==================

The nodex package can be useful in a multitude of scenarios. Since it's easy to use and fast to write complex node
graphs in code this means you can:

1. Prototype quickly
2. Maintain a readable code library
3. Write short code snippets for re-use
4. Create complex node graphs in code avoiding human error

Keeping that in mind it could really shine when you're developing an *autorigger* that is mostly code-based.

How does Nodex work?
====================

The concept behind Nodex
------------------------

The core idea behind Nodex is that most mathematical operations have a single piece of data as its result. The same goes
for many important mathematical operations when dealing with nodes.

Once you perform an operation on the Nodex that creates new nodes it returns a Nodex of the most important output
attribute of that node so you can directly operate on the resulting value. For example doing an addition between two
numerical Nodex instances returns the output attribute of a newly created plusMinusAverage node as a new Nodex instance.

.. code-block:: python

    from nodex.core import Nodex
    result = Nodex(1.0) + Nodex(2.0)
    print result

This means that you can directly chain a new operation on top of that.
This makes it possible to write a single line as a mathematical expression generating a complex node chain:

.. code-block:: python

    from nodex.core import Nodex
    x = Nodex(1)
    y = Nodex(2)
    result = ((x + (y*2)) / (x^2)) * 10.0

The Nodex class
---------------

The Nodex class has an initializer (geeks: ``__new__()``) that behaves like an abstract factory creating the correct
instance of a subclass that corresponds with that data, those subclasses are referred to as the implementations of the
**datatypes**

Each **datatype** has its own implementation of mathematical operations and methods that are specific to that data.
That's why you have access to Vector math functionality once you initialize the Nodex with something like ``[0, 0, 0]``.

If you check the type of the Nodex you'll see it's actually a ``nodex.datatypes.Vector``.

.. code-block:: python

    from nodex.core import Nodex
    n = Nodex([0, 0, 0]]
    print type(n)

