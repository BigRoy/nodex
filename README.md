# Nodex

This package defines a wrapping functionality to create and manage mathematical
node connections in Maya through Python scripting. The ease of access and method of using this
will help to write readable and maintainable code for node based graphs that require
a lot of mathematical processing.

![Nodex Logo](static/images/nodex_logo_256.png)

# Documentation

### Full documentation for Nodex:

- [http://www.colorbleed.nl/docs/nodex/master/](http://www.colorbleed.nl/docs/nodex/master/)

# Brief docs

## Node expressions for Maya

The core concept of the Nodex is that each node in the graph can have multiple inputs, but has a
single important output. This way the algorithm can be written as a single line of chained commands.

The process works by using an object called the ``Nodex``.

Upon initializing a Nodex you reference a value (its first argument). Since the Nodex has a magic initialization 
(factory within __new__) it will become the relevant datatype for the data you're referencing.

Then you can perform mathematical operations upon this Nodex with another
Nodex (thus other attributes/numbers) and it will automatically return a Nodex that references
the output attribute resulting from the created node graph.

Performable operations include mathematical operators that act directly on the Nodex instance, like:

- +, -, /, *, ^ for addition, subtraction, division, multiplication and power.
- ==, !=, >, >=, <, <= that will result in a 'condition' node.

Yet there's no boundary on what arguments one of the Nodex' inherited methods have so those could also
include easing the workflow for much more complex operations than those already provided.

That's why you'll also see (among others) **dot-product** and **cross-product** implementations work when dealing with
Vectors.

## Features


#### Returns the smallest calculated resulting attribute (3-Vector > 2-Vector > Scalar)

The Nodex will try to minimize the result/output based on the inputs. This means that when
you add two integers it will give you the output attribute (as Nodex) for a single float
attribute (output1D). But if you add two vectors together it will return the output3D from the
used plusMinusAverage node.

Note: This is of course only a valid statement for where this conversion is possible with the given
      Maya graph nodes.

#### Chain, chainery, chain-chain-cheroo

Since the output of each calculation with Nodex instances returns a new Nodex wrapping the calculation's output
attribute you can write a chain of calculations. Of course you're free to stop take the resulting node midway, store
it in a variable and use it's output for a multitude of node trees.

#### Smart set/connect for attributes

Using an input value or attribute it will try to guess how to connect it to the input attributes
for a mathemical node based on the smaller input element (in dimensions) similar to above.
This means adding together a float attribute with a vector attribute will actually result in
a Vector where each component has the scalar added like this:

    float + vector        = vector + vector                   = vector output
    0.5 + [0.3, -1, 10.1] = [0.5, 0.5, 0.5] + [0.3, -1, 10.1] = [0.8, -0.5, 10.6]


## Code Samples

Multiply two attributes and connect the output value

```python
mult = Nodex("pSphere1.translateX") * Nodex("pSphere1.translateY")
mult.connectTo( Nodex("pSphere1.translateZ") )
```

---

Add together multiple attributes (sum more than two values) and connect the result

```python
result = Math.sum("pSphere1.translateX", "pSphere1.translateY", "pSphere1.translateZ", 1.0)
result.connectTo( Nodex("pSphere1.scaleX") )
```

---

Clamp an attribute and connect it

```python
Nodex.clamp("pSphere1.translateX", min=0, max=1, output="pSphere1.translateY")
```

---

Complex operations become a bit more readable

```python
(Nodex("pSphere.translateX") * 2) + 0.5
```

---

Using the Nodex's mixed array instantiation

```python
nodex = Nodex([1, 0, "pSphere1.translateX"]) * 3
print nodex.value()
```

This will print `[3, 0, 15]` if *pSphere1.translateX* is a value of 5.

---

Or perform a calculation through Maya nodes and clean up the Nodex tree afterwards

```python
# The *MayaDeleteNewNodes* context manager is not included in the Nodex package but should be trivial to implement
with MayaDeleteNewNodes():
    nodex = (Nodex(1) + Nodex("pSphere1.translateX")) / Nodex("pSphere2.translateY")
    value = nodex.value()
```

---

### Matrix Datatype

##### (>0.2.0) Matrix node creations in Maya are possible with Python using Nodex

No more choosing which pill to take; take both red and blue.

```python
matrix = pymel.core.datatypes.Matrix()
nodex = Nodex(matrix)

# Convert the matrix into the local space of object `redPill`
redPill_matrix = Nodex("redPill.worldMatrix[0]")
local_mat = matrix * redPill_matrix.inverse()

# Decompose and directly connect to object `bluePill`
local_mat.decompose(translate="bluePill.translate",
                    rotate="bluePill.rotate",
                    scale="bluePill.scale")
```

---

##### Setting up a simple *Matrix constraint* relationship between two objects with Nodex

Snap the `src` object to the `target` object. 
This will also work if they are NOT under the same parent.

```python
sel = pymel.core.ls(selection=True)
target = sel[0]
src = sel[1] # this will move towards the target

targetMat = Nodex(target.attr("worldMatrix[0]"))
srcParentInvMat = Nodex(src.attr("parentInverseMatrix[0]"))

localMat = targetMat * srcParentInvMat
localMat.decompose(translate=src.attr('translate'), 
                   rotate=src.attr('rotate'),
                   scale=src.attr('scale'))
```
---

### Vector datatype

##### (>0.2.1) Vector math in Maya with nodes is possible with Python using Nodex

Have a blast *normalizing* your vectors!

```python
vector = pymel.core.datatypes.Vector(10, 10, 0)
v = Nodex(vector)

# Let's get a point on the unit sphere.
v = v.normal()

# Let's put that point on a sphere of radius 5
v *= [5.0, 5.0, 5.0]

# Let's offset it by the translate of another node
v += Nodex('otherNode.translate')

# And use it to drive this node.
v.connect('thisNode.translate')
```

##### The available methods for the Vector datatype are (outside of those inherited from Array):

```python
# cross product with another vector
vector.cross(otherVector) 

# dot product with another vector
vector.dot(otherVector) 

# normalize the vector
vector.normal()

# angle between two vectors
vector.angleTo(otherVector)

# distance between two vectors (as points)
vector.distanceTo(otherVector)

# length of the vector
vector.length()

# squared length of the vector (uses two nodes)
vector.squareLength()
```

---