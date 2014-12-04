# Node Expression for maya.

This class defines a simple wrapping functionality to create and manage mathematical
node connections in Maya through scripting. The ease of access and method of using this
will help to write readable and maintainable code for node based graphs that require
a lot of mathematical processing.

The process works by using an object called the ``Nodex``.

Upon initializing a Nodex you reference a value, which is either a real value (numerical)
or an attribute. Then you can perform mathematical operations upon this Nnodex with another
Nodex (thus other attributes/numbers) and it will automatically return a Nodex that references
the output attribute resulting from the created node graph.

Basically it either:
    1) Operates on output attributes so it can quickly connect it to another Nodex
    2) Or references a value so that it can easily assign it into another Nodex.

Performable operations include mathematical operators like: +, -, /, *, ^ for addition,
subtraction, division, multiplication and power. Then there are comparison operators like
==, !=, >, >=, <, <= that will result in a 'condition' node. All overridden operator functionality
of the Nodex can also be peformed with its staticmethods, and more. Those other operations include:
- average (plusMinusAverage)
- clamp (clamp)
- angleBetween (angleBetween)
- .. And the list goes on (and could easily be extended)

The core concept of the Nodex is that each node in the graph can have multiple inputs, but has a
single important output. This way the algorithm can be written as a single line of chained commands.
Yet there's no boundary on what arguments one of the Nodex' staticmethods have so those could also
include easing the workflow for much more complex operations than those already provided.

## Features

###    Returns the smallest calculated resulting attribute (3-Vector > 2-Vector > Scalar)

The Nodex will try to minimize the result/output based on the inputs. This means that when
you add two integers it will give you the output attribute (as Nodex) for a single float
attribute (output1D). But if you add two vectors together it will return the output3D from the
used plusMinusAverage node.

Note: This is of course only a valid statement for where this conversion is possible with the given
      Maya graph nodes.


###    Smart set/connect for attributes

Using an input value or attribute it will try to guess how to connect it to the input attributes
for a mathemical node based on the smaller input element (in dimensions) similar to above.
This means adding together a float attribute with a vector attribute will actually result in
a Vector where each component has the scalar added like this:

    float + vector        = vector + vector                   = vector output
    0.5 + [0.3, -1, 10.1] = [0.5, 0.5, 0.5] + [0.3, -1, 10.1] = [0.8, -0.5, 10.6]

NOTE:
For all methods on Nodex the type of the output is based on the inputs, thus it will never 'adapt'
to the type of output attribute that you're trying to connect to if directly connected with one of
its staticmethods. An **EXCEPTION** is the Nodex().connectTo() method will try to adapt when possible!


#    Code Samples

Examples:
    # 1. Multiply two attributes and connect the output value
    >> mult = Nodex("pSphere1.translateX") * Nodex("pSphere1.translateY")
    >> mult.connectTo( Nodex("pSphere1.translateZ") )

    # 2. Add together multiple attributes (sum more than two values) and connect the result
    >> result = Nodex.sum("pSphere1.translateX", "pSphere1.translateY", "pSphere1.translateZ", 1.0)
    >> result.connectTo( Nodex("pSphere1.scaleX") )

    # 3. Clamp an attribute and connect it
    >> Nodex.clamp("pSphere1.translateX", min=0, max=1, output="pSphere1.translateY")

    # 4. Complex operations become a bit more readable
    >> (Nodex("pSphere.translateX") * 2) + 0.5

    # 5. Or using your multiplyDivide now quickly in a multitiude of ways
    >> Nodex([1, 0, "pSphere.translateX"]) * 3