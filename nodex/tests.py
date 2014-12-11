from nodex.core import *
import unittest
import nodex.datatypes


class TestNodexMethods(unittest.TestCase):
    def setUp(self):
        # TODO: Add little prompt dialog that this will force a new scene to open
        #       Thus user might lose current work. :)
        #       Basically prompt to SAVE!
        mc.file(new=True, force=True)
        mc.polySphere()  # "pSphere1"

    def test_types(self):
        self.assertEqual(type(Nodex(True)), nodex.datatypes.Boolean)
        self.assertEqual(type(Nodex(False)), nodex.datatypes.Boolean)
        self.assertEqual(type(Nodex(0.1)), nodex.datatypes.Float)
        self.assertEqual(type(Nodex(1.0)), nodex.datatypes.Float)
        self.assertEqual(type(Nodex(-0.595412)), nodex.datatypes.Float)
        self.assertEqual(type(Nodex(1)), nodex.datatypes.Integer)
        self.assertEqual(type(Nodex(-9)), nodex.datatypes.Integer)
        self.assertEqual(type(Nodex(1231)), nodex.datatypes.Integer)

    def test_getitem(self):
        n = Nodex("pSphere1.t")
        mc.xform("pSphere1", t=(0, 1, 2), absolute=True, objectSpace=True)
        self.assertEqual(n[0].dimensions(), 1)
        self.assertEqual(n[:-1].dimensions(), 2)
        self.assertEqual(n[:-1].value(), (0, 1))

        # This is a tricky one since the slicing returns a one tuple referencing Nodex.
        # once grabbing the value it returns it within the one tuple.
        # TODO: Decide whether this is expected behavior; if not we need to redesign that part of the
        #       __getitem__ implementation
        self.assertEqual(n[1:-1].dimensions(), 1)
        self.assertEqual(n[1:-1].value(), (1.0,))

    def test_dimensions(self):
        self.assertEqual(Nodex(1).dimensions(), 1)
        self.assertEqual(Nodex([1, 1]).dimensions(), 2)
        self.assertEqual(Nodex([1, 1, 1]).dimensions(), 3)
        self.assertEqual(Nodex([1, 1, 1, 1]).dimensions(), 4)
        self.assertEqual(Nodex([1]*10).dimensions(), 10)
        self.assertEqual(Nodex("pSphere1.t").dimensions(), 3)
        self.assertEqual(Nodex("pSphere1.tx").dimensions(), 1)
        self.assertEqual(Nodex("pSphere1.v").dimensions(), 1)

    def test_comparisons(self):
        """
            Test if the comparisons have the correct outputs.
        """
        n = (Nodex(3) == Nodex(2))
        self.assertEqual(n.value(), 0.0)

        n = (Nodex(2) == Nodex(2))
        self.assertEqual(n.value(), 1.0)

        # ==
        mc.xform("pSphere1", t=(3, 3, 0), absolute=True, objectSpace=True)
        n = (Nodex("pSphere1.tx") == Nodex("pSphere1.ty"))
        self.assertEqual(n.value(), 1)
        mc.xform("pSphere1", t=(3, 4, 0), absolute=True, objectSpace=True)
        self.assertEqual(n.value(), 0)

        # !=
        x_not_y = (Nodex("pSphere1.tx") != Nodex("pSphere1.ty"))
        mc.xform("pSphere1", t=(0, 0, 0), absolute=True, objectSpace=True)
        self.assertEqual(x_not_y.value(), 0)
        mc.xform("pSphere1", t=(0, 1, 0), absolute=True, objectSpace=True)
        self.assertEqual(x_not_y.value(), 1)

        # >
        x_bigger_y = (Nodex("pSphere1.tx") > Nodex("pSphere1.ty"))
        mc.xform("pSphere1", t=(0.5, 0.1, 0), absolute=True, objectSpace=True)
        self.assertEqual(x_bigger_y.value(), 1)
        mc.xform("pSphere1", t=(0.1, 0.5, 0), absolute=True, objectSpace=True)
        self.assertEqual(x_bigger_y.value(), 0)
        mc.xform("pSphere1", t=(0, 5, 0), absolute=True, objectSpace=True)
        self.assertEqual(x_bigger_y.value(), 0)
        mc.xform("pSphere1", t=(-49, -50, 0), absolute=True, objectSpace=True)
        self.assertEqual(x_bigger_y.value(), 1)

        # <
        x_smaller_y = (Nodex("pSphere1.tx") < Nodex("pSphere1.ty"))
        mc.xform("pSphere1", t=(-5, 0, 0), absolute=True, objectSpace=True)
        self.assertEqual(x_smaller_y.value(), 1)
        mc.xform("pSphere1", t=(1.1, 1, 0), absolute=True, objectSpace=True)
        self.assertEqual(x_smaller_y.value(), 0)
        mc.xform("pSphere1", t=(0, 0.1, 0), absolute=True, objectSpace=True)
        self.assertEqual(x_smaller_y.value(), 1)
        mc.xform("pSphere1", t=(-50, -49, 0), absolute=True, objectSpace=True)
        self.assertEqual(x_smaller_y.value(), 1)

        # Graph: Check if x, y, z are all the same value
        xy = (Nodex("pSphere1.tx") == Nodex("pSphere1.ty"))
        yz = (Nodex("pSphere1.ty") == Nodex("pSphere1.tz"))
        xz = (Nodex("pSphere1.tx") == Nodex("pSphere1.tz"))
        sum = Nodex.sum(xy, yz, xz) # sum in a single node
        cond_all = (sum == 3)

        mc.xform("pSphere1", t=(0, 0, 0), absolute=True, objectSpace=True)
        self.assertEqual(cond_all.value(), 1)
        mc.xform("pSphere1", t=(1, 0, 0), absolute=True, objectSpace=True)
        self.assertEqual(cond_all.value(), 0)
        mc.xform("pSphere1", t=(0, 1, 0), absolute=True, objectSpace=True)
        self.assertEqual(cond_all.value(), 0)
        mc.xform("pSphere1", t=(0, 0, 1), absolute=True, objectSpace=True)

        self.assertEqual(cond_all.value(), 0)
        mc.xform("pSphere1", t=(15, 15, 15), absolute=True, objectSpace=True)
        self.assertEqual(cond_all.value(), 1)
        mc.xform("pSphere1", t=(0.001, 0, 0), absolute=True, objectSpace=True)
        self.assertEqual(cond_all.value(), 0)

        # Reset the sphere
        mc.xform("pSphere1", t=(0, 0, 0), absolute=True, objectSpace=True)

    def test_additions(self):
        s = Nodex(1.0) + Nodex(2.0)
        self.assertEqual(s.value(), 3.0)
        s += Nodex(5.0)
        self.assertEquals(s.value(), 8.0)
        s = s + Nodex(3.0) - Nodex(9.0)
        self.assertEqual(s.value(), 2.0)

        s = Nodex([0, 1, 2]) + Nodex([0, 2, 1])
        self.assertEqual(s.value(), (0.0, 3.0, 3.0))
        s += Nodex("pSphere1.t")
        mc.xform("pSphere1", t=(0, 0, 0), ws=1)
        self.assertEqual(s.value(), (0.0, 3.0, 3.0))

        mc.xform("pSphere1", t=(-4.5, 7.0, 0.5), ws=1)
        self.assertEqual(s.value(), (-4.5, 10.0, 3.5))

        mc.xform("pSphere1", t=(-10.0, 5.0, 1000.0), ws=1)
        self.assertEqual(s.value(), (-10.0, 8.0, 1003.0))

        v = s.value()
        s -= Nodex(v)
        self.assertEqual(s.value(), (0.0, 0.0, 0.0))

        s += [3, 3, 3] # implicit conversion to Nodex()
        self.assertEqual(s.value(), (3.0, 3.0, 3.0))


if __name__ == '__main__':
    unittest.main()
