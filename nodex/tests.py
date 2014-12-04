from nodex.core import *
import unittest


class TestNodexMethods(unittest.TestCase):
    def setUp(self):
        # TODO: Add little prompt dialog that this will force a new scene to open
        #       Thus user might lose current work. :)
        #       Basically prompt to SAVE!
        mc.file(new=True, force=True)
        mc.polySphere()  # "pSphere1"

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
        self.assertEqual(n.value(), 0)
        n = (Nodex(2) == Nodex(2))
        self.assertEqual(n.value(), 0)

        mc.xform("pSphere1", t=(3, 3, 0), absolute=True, objectSpace=True)
        n = (Nodex("pSphere1.tx") == Nodex("pSphere1.ty"))
        self.assertEqual(n.value(), 1)
        mc.xform("pSphere1", t=(3, 4, 0), absolute=True, objectSpace=True)
        self.assertEqual(n.value(), 0)

        # Graph: Check if x, y, z are all the same value
        xy = (Nodex("pSphere1.tx") == Nodex("pSphere1.ty"))
        yz = (Nodex("pSphere1.ty") == Nodex("pSphere1.tz"))
        xz = (Nodex("pSphere1.tx") == Nodex("pSphere1.tz"))
        sum = xy + yz + xz
        cond_all = (sum == 3)

        mc.xform("pSphere1", t=(0, 0, 0), absolute=True, objectSpace=True)
        self.assertEqual(n.value(), 1)
        mc.xform("pSphere1", t=(1, 0, 0), absolute=True, objectSpace=True)
        self.assertEqual(n.value(), 0)
        mc.xform("pSphere1", t=(0, 1, 0), absolute=True, objectSpace=True)
        self.assertEqual(n.value(), 0)
        mc.xform("pSphere1", t=(0, 0, 1), absolute=True, objectSpace=True)
        self.assertEqual(n.value(), 0)
        mc.xform("pSphere1", t=(15, 15, 15), absolute=True, objectSpace=True)
        self.assertEqual(n.value(), 1)
        mc.xform("pSphere1", t=(0.001, 0, 0), absolute=True, objectSpace=True)
        self.assertEqual(n.value(), 0)

        # Reset the sphere
        mc.xform("pSphere1", t=(0, 0, 0), absolute=True, objectSpace=True)

    def test_additions(self):
        pass
        #s = Nodex(1) + Nodex(2)
        #print s.value()

if __name__ == '__main__':
    unittest.main()
