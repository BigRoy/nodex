from nodex.core import Nodex, Math, UndefinedNodexError
import unittest
import nodex.datatypes
import pymel.core
import maya.cmds as mc
import time
import logging

logger = logging.getLogger(__name__)


class speedMeasure(object):
    def __init__(self, max_duration, msg=None):
        self._max_duration = max_duration
        self._msg = msg
        self._start = 0

    def __enter__(self):
        self._start = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._end = time.time()
        self._duration = self._end - self._start
        if self._duration > self._max_duration:
            raise AssertionError("{0} is longer than {1}. {2}".format(self._duration, self._max_duration, self._msg))
        else:
            logger.debug("speedMeasure: {0}s <= {1}s; msg: {2}".format(self._duration, self._max_duration, self._msg))


class TestNodexSpeed(unittest.TestCase):
    """ Ensuring code changes don't slow the Nodex down too much """

    def test_long_array(self):
        """ This is a good test since each element within the Array gets converted to a single Nodex() element.
            So it calls the Nodex __new__ method many times.
        """
        with speedMeasure(0.3, msg="array: list multiplied"):
            Nodex([1]*10000)

        with speedMeasure(0.3, msg="array: range"):
            Nodex(range(10000))

    def test_many_matrices(self):

        l = [0]*16
        with speedMeasure(0.06, msg="init matrices"):
            for x in range(250):
                m = Nodex(l)

        with speedMeasure(0.25, msg="init matrices & getting values"):
            for x in range(50):
                m = Nodex(l)
                m.value()

        with speedMeasure(0.06, msg="init matrices explicit"):
            for x in range(250):
                m = nodex.datatypes.Matrix(l)


class TestNodexTypes(unittest.TestCase):
    def test_type_init(self):
        # boolean
        self.assertEqual(type(Nodex(True)), nodex.datatypes.Boolean)
        self.assertEqual(type(Nodex(False)), nodex.datatypes.Boolean)

        # float
        self.assertEqual(type(Nodex(0.1)), nodex.datatypes.Float)
        self.assertEqual(type(Nodex(1.0)), nodex.datatypes.Float)
        self.assertEqual(type(Nodex(-0.595412)), nodex.datatypes.Float)

        # integer
        self.assertEqual(type(Nodex(1)), nodex.datatypes.Integer)
        self.assertEqual(type(Nodex(-9)), nodex.datatypes.Integer)
        self.assertEqual(type(Nodex(1231)), nodex.datatypes.Integer)

        # array
        with self.assertRaises(UndefinedNodexError):
            Nodex([])

        self.assertEqual(type(Nodex([10]*10)), nodex.datatypes.Array)

        # TODO: Enable Vector type tests when Vector is implemented
        #self.assertEqual(type(Nodex([1,2,3])), nodex.datatypes.Vector)

        # matrix
        self.assertEqual(type(Nodex([0]*16)), nodex.datatypes.Matrix)

        # none-types
        with self.assertRaises(TypeError):
            Nodex(None)

        # default values
        nodex.datatypes.Boolean()
        nodex.datatypes.Float()
        nodex.datatypes.Integer()
        nodex.datatypes.Matrix()


class TestNodexMethods(unittest.TestCase):
    def setUp(self):
        # TODO: Add little prompt dialog that this will force a new scene to open
        #       Thus user might lose current work. :)
        #       Basically prompt to SAVE!
        mc.file(new=True, force=True)
        mc.polySphere()  # "pSphere1"

    def test_multiplyDivide(self):
        # TODO: This will fail. Implement multiplyDivide correctly.
        # Current issue is with 'isAttribute()' implementation on Arrays.
        result = nodex.datatypes.Float() * nodex.datatypes.Integer()
        self.assertEqual(result.value(), 0.0)
        result += 1
        self.assertEqual(result.value(), 1.0)
        result *= 15
        self.assertEqual(result.value(), 15.0)
        result /= 2.0
        self.assertEqual(result.value(), 7.5)
        result ^= 2
        self.assertEqual(result.value(), 7.5*7.5)

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

        # Check if long arrays work as execpted
        self.assertEqual(Nodex([1]*10000).value(), tuple([1] * 10000))
        v = tuple(range(150))
        self.assertEqual(Nodex(v).value(), v)

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
        sum = Math.sum(xy, yz, xz) # sum in a single node
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

        s += [3, 3, 3]   # implicit conversion to Nodex()
        self.assertEqual(s.value(), (3.0, 3.0, 3.0))


class TestMatrixMethods(unittest.TestCase):
    def setUp(self):
        # TODO: Add little prompt dialog that this will force a new scene to open
        #       Thus user might lose current work. :)
        #       Basically prompt to SAVE!
        mc.file(new=True, force=True)

    def test_matrix_init(self):
        import maya.OpenMaya
        import maya.api.OpenMaya

        # Pymel
        m = Nodex(pymel.core.datatypes.Matrix())
        self.assertIsInstance(m, nodex.datatypes.Matrix)
        m = Nodex(pymel.core.datatypes.FloatMatrix())
        self.assertIsInstance(m, nodex.datatypes.Matrix)

        # Maya Python API
        m = Nodex(maya.OpenMaya.MFloatMatrix())
        self.assertIsInstance(m, nodex.datatypes.Matrix)
        m = Nodex(maya.OpenMaya.MMatrix())
        self.assertIsInstance(m, nodex.datatypes.Matrix)

        # Maya Python API 2.0
        m = Nodex(maya.api.OpenMaya.MFloatMatrix())
        self.assertIsInstance(m, nodex.datatypes.Matrix)
        m = Nodex(maya.api.OpenMaya.MMatrix())
        self.assertIsInstance(m, nodex.datatypes.Matrix)
        m = Nodex(maya.OpenMaya.MFloatMatrix())
        self.assertIsInstance(m, nodex.datatypes.Matrix)

        # nested list
        mat = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        m = Nodex(mat)
        self.assertIsInstance(m, nodex.datatypes.Matrix)

        # list
        mat = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.assertIsInstance(m, nodex.datatypes.Matrix)

    def test_matrix_inverse(self):

        # Create some test nodes
        src = pymel.core.polySphere(name='src')[0]
        srcGrp = pymel.core.group(src)

        # Some randomly chosen translate values
        srcGrp.setTranslation((9, 15, 0.01))

        m = Nodex(src.attr('worldMatrix[0]'))
        m_inv = m.inverse()
        parent_m = Nodex(srcGrp.attr('worldMatrix[0]'))
        parent_m_inv = parent_m.inverse()
        parent_m_inv_inv = parent_m_inv.inverse()

        # Check outputs
        tolerance = 1e-10

        m1 = parent_m_inv.value()
        m2 = Nodex(src.attr('parentInverseMatrix[0]')).value()
        self.assertTrue(m1.isEquivalent(m2, tol=tolerance))
        m1 = parent_m_inv_inv.value()
        m2 = Nodex(parent_m.value()).value()
        self.assertTrue(m1.isEquivalent(m2, tol=tolerance))

        # Update the nodes
        old_parent_m_inv_inv_value = m1
        src.setRotation((9, 15, 0.01))
        srcGrp.setScale((9, 15, 0.01))

        m1 = parent_m_inv.value()
        m2 = Nodex(src.attr('parentInverseMatrix[0]')).value()
        self.assertTrue(m1.isEquivalent(m2, tol=tolerance))
        m1 = parent_m_inv_inv.value()
        m2 = Nodex(parent_m.value()).value()
        self.assertTrue(m1.isEquivalent(m2, tol=tolerance))

        # Ensure the output of the nodes has actually changed
        new_parent_m_inv_inv_value = m1
        self.assertFalse(old_parent_m_inv_inv_value.isEquivalent(new_parent_m_inv_inv_value))

        pymel.core.delete([src, srcGrp])

    def test_matrix_constraint(self):
        """
            Let's put another sphere to the same position as the original sphere
            even if the spheres are not under the same parent by using the worldMatrix
            and the parentInverseMatrix
        """
        # Create some test nodes
        src = pymel.core.polySphere(name='src')[0]           # the source will
        target = pymel.core.polySphere(name='target')[0]     # move to this target
        srcGrp = pymel.core.group(src)
        targetGrp = pymel.core.group(srcGrp)

        # Some randomly chosen translate values
        srcGrp.setTranslation((0, 10, 0))
        targetGrp.setTranslation((0.5, 14.0, -129))
        target.setTranslation((0.1, -0.3, 0.8))

        # The actual node creation (sweet-sweet-Nodex shows its power here!)
        targetMat = Nodex(target.attr("worldMatrix[0]"))
        srcParentInvMat = Nodex(src.attr("parentInverseMatrix[0]"))

        localMat = targetMat * srcParentInvMat
        localMat.decompose(translate=src.attr('translate'))

        # Let's test!
        # Now the world position should always match even if grp was moved
        # We need a tolerance because Matrix math and computers are not 100% exact due to floating point precision
        # errors. (This is not a fault in Nodex, it's just the way computers work thus also the Maya matrix nodes!)
        tolerance = 1e-10

        targetPos = target.getTranslation(space='world')
        srcPos = src.getTranslation(space='world')
        self.assertTrue(targetPos.isEquivalent(srcPos, tol=tolerance))

        # With non-uniform scaled group above src
        srcGrp.setScale((0.1, 10, 10))
        targetPos = target.getTranslation(space='world')
        srcPos = src.getTranslation(space='world')
        self.assertTrue(targetPos.isEquivalent(srcPos, tol=tolerance))

        # With rotated parent group above target
        targetGrp.setRotation((-0.25241, 45, 90))
        targetPos = target.getTranslation(space='world')
        srcPos = src.getTranslation(space='world')
        self.assertTrue(targetPos.isEquivalent(srcPos, tol=tolerance))

        pymel.core.delete([src, target, srcGrp, targetGrp])

    def test_composeMatrix(self):

        # Create test node
        src = pymel.core.polySphere(name='src')[0]           # the source will

        def check_node_vs_composed_matrix(node, t, r, s):
            tolerance = 1e-10

            node.setTranslation(t, space='object')
            node.setRotation(r, space='object')
            node.setScale(s, space='object')
            matrix = nodex.datatypes.Matrix.compose(translate=t, rotate=r, scale=s)
            self.assertTrue(node.getMatrix().isEquivalent(matrix.value(), tol=tolerance))

        t = (0, 12.01, 51)
        r = (0.5, 43, -9)
        s = (0.1, 0.2, 0.3)
        check_node_vs_composed_matrix(src, t, r, s)

        t = (100, 50, -100)
        r = (0.001, 19, 45231)
        s = (1, 1, 1)
        check_node_vs_composed_matrix(src, t, r, s)

        t = (0, 0, 0)
        r = (0, 0, 0)
        s = (1, 1, 1)
        check_node_vs_composed_matrix(src, t, r, s)






if __name__ == '__main__':
    unittest.main()
