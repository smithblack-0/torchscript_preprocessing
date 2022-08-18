"""

Test the fixtures behind the construction database

Objectives:

* module can reconstruct meaningful and similar code
*  can edit chain once constructed
*  can be used to meaningfully track down edit node on inferral

"""
import unittest

import astroid

from src import construction_database

class test_linked_lists(unittest.TestCase):
    """
    A test case for the utilized linked
    list used to store information.
    """
    def test_firstlast(self):
        """Test the first and last properties are effective"""
        a = construction_database.DoubleLinkedList()
        b = construction_database.DoubleLinkedList()
        c = construction_database.DoubleLinkedList()
        d = construction_database.DoubleLinkedList()

        a.child = b
        b.child = c
        c.child = d

        self.assertTrue(a.first is a)
        print(b.child)
        print(a.last is b)
        self.assertTrue(a.last is d)
        self.assertTrue(b.first is a)
        self.assertTrue(b.last is d)
        self.assertTrue(a.last.first is a)
        self.assertTrue(a.last.last is d)

    def test_insertion(self):
        """ test insertion is working without issue"""
        a = construction_database.DoubleLinkedList()
        b = construction_database.DoubleLinkedList()
        c = construction_database.DoubleLinkedList()
        d = construction_database.DoubleLinkedList()

        x = construction_database.DoubleLinkedList()
        y = construction_database.DoubleLinkedList()
        z = construction_database.DoubleLinkedList()

        a.child = b
        b.child = c
        c.child = d

        x.child = y
        y.child = z

        b.insert(x)
        self.assertTrue(b.parent is z)
        self.assertTrue(a.child is x)

    def test_linkage(self):
        """Test that forward and backward linkages are behaving sanely. """
        a = construction_database.DoubleLinkedList()
        b = construction_database.DoubleLinkedList()
        c = construction_database.DoubleLinkedList()

        #Test basic attachment
        a.child = b
        self.assertTrue(a.child is b)
        self.assertTrue(b.parent is a)

        #Test automatic freeing
        a.child = c
        self.assertTrue(a.child is c)
        self.assertTrue(c.parent is a)
        self.assertTrue(b.parent is None)

        #Test assign by previous
        c.parent = b
        self.assertTrue(c.parent is b)
        self.assertTrue(b.child is c)
        self.assertTrue(a.child is None)

    def test_creation(self):
        construction_database.DoubleLinkedList()

class testActions(unittest.TestCase):
    def test_creation(self):
        """tests if you can create these at all"""

        start = construction_database.ActionLinkNode()

        start.create("test", astroid.NodeNG)
        start.emplace("test", "test")
