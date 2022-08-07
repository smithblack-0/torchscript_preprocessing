"""
Test units for the data structures.

Data structures consist of things like
code blocks or stubs.

"""

import unittest
from src import datastructures
from src import errors


class test_DLList(unittest.TestCase):
    """
    A test case for the utilized linked
    list used to store information.
    """
    def test_append(self):
        """Test that appending works"""
        a = datastructures.DLList()
        b = datastructures.DLList()
        c = datastructures.DLList()

        assert a.next is None
        a.append(b)
        a.append(c)

        self.assertTrue(b.next is c)

    def test_iter(self):
        """Test that iteration proceeds as normal through the"""
        a = datastructures.DLList()
        b = datastructures.DLList()
        c = datastructures.DLList()

        co_iter = [a, b, c]
        for item1, item2 in zip(iter(a), co_iter):
            self.assertTrue(item1 is item2)
        for item in a:
            pass

    def test_linkage(self):
        """Test that forward and backward linkages are behaving sanely. """
        a = datastructures.DLList()
        b = datastructures.DLList()
        c = datastructures.DLList()

        #Test basic attachment
        a.next = b
        self.assertTrue(a.next is b)
        self.assertTrue(b.last is a)

        #Test automatic freeing
        a.next = c
        self.assertTrue(a.next is c)
        self.assertTrue(c.last is a)
        self.assertTrue(b.last is None)

        #Test assign by previous
        c.last = b
        self.assertTrue(c.last is b)
        self.assertTrue(b.next is c)
        self.assertTrue(a.next is None)

    def test_creation(self):
        datastructures.DLList()


class unit_CodeBlock(unittest.TestCase):
    class range_Mockup:
        """A mockup for a sourcerange"""
        def __init__(self, start, end):
            self.start = start
            self.end = end

    def test_linked(self):
        """test the ability to link together, and use, lists"""

        source = ["source1", "source2", "source3"]
        compound = "".join(source)
        startat = [compound.index(item) for item in source]
        endat = [compound.index(item) + len(item) for item in source]

        #Construct test features
        def setup(i):
            def callback(tp):
                return Exception(i)
            return callback


        blocks = [datastructures.CodeBlock(item,setup(i))
                  for i, item in enumerate(source)]
        a, b, c = blocks
        a.next = b
        b.next = c


        #Test read
        self.assertTrue(a.read() == compound)

        #Test char block functionality.
        for item, start, end in zip(a, startat, endat):
            self.assertTrue(item.start == start)
            self.assertTrue(item.end == end)

        #Test exception fetch functionality
        suite = [self.range_Mockup(start, end) for start, end in zip(startat, endat)]
        expect = [Exception(i) for i in range(3)]

        suite += [self.range_Mockup(start+2, end-2) for start, end in zip(startat, endat)]
        expect += [Exception(i) for i in range(3)]

        for r, expectation in zip(suite, expect):
            err = a.fetch_exception(None, r)
            self.assertTrue(type(err) == expectation.__class__)
            self.assertTrue(err.args[0] == expectation.args[0])

    def test_unlinked(self):
        """Test the ability to use lists at all"""
        source = "Ladededadeti"
        block = datastructures.CodeBlock(source, Exception)

        #Test read
        output = block.read()
        self.assertTrue(source == output)

        #Test exception lookup resolving
        r_true = self.range_Mockup(3, 7)
        t_exc = block.fetch_exception(None, r_true)
        self.assertTrue(isinstance(t_exc, Exception))

        #Test exception lookup failing
        r_false = self.range_Mockup(3000, 30054)
        f_exc = block.fetch_exception(None, r_false)
        self.assertTrue(isinstance(f_exc, errors.UnhandledPreprocessingError))
