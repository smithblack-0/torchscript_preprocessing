"""

Test the fixtures behind the construction database

Objectives:

* module can reconstruct meaningful and similar code
*  can edit chain once constructed
*  can be used to meaningfully track down edit node on inferral

"""
import unittest
from typing import Generator, List

import astroid
import ast
import inspect


from src import build

class test_linked_lists(unittest.TestCase):
    """
    A test case for the utilized linked
    list used to store information.
    """
    def test_firstlast(self):
        """Test the first and last properties are effective"""
        a = build.DoubleLinkedList()
        b = build.DoubleLinkedList()
        c = build.DoubleLinkedList()
        d = build.DoubleLinkedList()

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
        a = build.DoubleLinkedList()
        b = build.DoubleLinkedList()
        c = build.DoubleLinkedList()
        d = build.DoubleLinkedList()

        x = build.DoubleLinkedList()
        y = build.DoubleLinkedList()
        z = build.DoubleLinkedList()

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
        a = build.DoubleLinkedList()
        b = build.DoubleLinkedList()
        c = build.DoubleLinkedList()

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
        build.DoubleLinkedList()

class testActions(unittest.TestCase):
    def test_creation(self):
        """tests if you can create these at all"""

        start = build.BuildNode()
        start.create("test", astroid.NodeNG)
        start.emplace("test", "test")
    def test_basic_compilation(self):
        def test_target():
            print("Hello world")

        source = inspect.getsource(test_target)
        tree = astroid.parse(source)

        NodeBuilder = build.BuildNode()
        stack: List[Tuple[Generator[astroid.NodeNG], astroid.NodeNG]] = []
        generator = tree.get_children()
        while True:
            try:
                child = next(generator)
                stack.append((generator, child))
                generator = child.get_children()
            except StopIteration:





