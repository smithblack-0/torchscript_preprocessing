"""

Test fixtures for inference.

Used for the purposes of performing test
driven development

"""
import inspect
import unittest
import ast
import astroid

from textwrap import dedent
from typing import Callable, Generator, Optional
from src import builder

def capture(node: astroid.NodeNG,
            predicate: Callable[[astroid.NodeNG], bool],
            stop: Optional[Callable[[astroid.NodeNG], bool]] = None

            )->Generator[astroid.NodeNG, None, None]:
    """Captures and returns nodes matching predicate"""
    stack = []
    generator = node.get_children()
    while True:
        try:
            child = next(generator)
            if isinstance(child, astroid.NodeNG):
                stack.append((child, generator))
                generator = child.get_children()
        except StopIteration:
            if len(stack) == 0:
                break
            child, generator = stack.pop()
            if stop is not None and stop(child):
                break
            if predicate(child):
                yield  child



class test_variable_inference(unittest.TestCase):
    """
    Tests ability to infer the
    code defining various variables
    """
    def test_simple_inference(self):
        """Tests ability to infer correct node when node is found
        immediately prior in code"""

        def scope():
            item = 4
            item

        def sought_predicate(node: astroid.NodeNG):
            if not isinstance(node, astroid.Const):
                return False
            return True
        def start_predicate(node: astroid.NodeNG):
            if not isinstance(node, astroid.Name):
                return False
            return True


        source = inspect.getsource(scope)
        source = dedent(source)
        asttree = astroid.parse(source)

        sought = next(capture(asttree, sought_predicate))
        start = next(capture(asttree, start_predicate))
        print(next(start.infer()))
        self.assertTrue(next(start.infer()) is sought)

    def test_excluding_scope_inference(self):
        """Test inference when crossing a bunch of closed over scopes """

        def scope():
            item = 6
            def interfere_as_function():
                """Contains a variable which may interfere"""
                item = 7
            class interfere_as_class():
                """Contains a variable which may interfere"""
                item = 8
            item

        def sought_predicate(node: astroid.NodeNG):
            if not isinstance(node, astroid.Const):
                return False
            return True
        def start_predicate(node: astroid.NodeNG):
            if not isinstance(node, astroid.Name):
                return False
            return True

        source = inspect.getsource(scope)
        source = dedent(source)
        asttree = astroid.parse(source)

        sought = next(capture(asttree, sought_predicate))
        start = next(capture(asttree, start_predicate))
        print(next(start.infer()))
        self.assertTrue(next(start.infer()) is sought)


        source = inspect.getsource(scope)
        source = dedent(source)
        asttree = astroid.parse(source)
        sought = next(capture(asttree, sought_predicate))
        start = next(capture(asttree, start_predicate))
        self.assertTrue(next(start.infer()) is sought)



class test_class_inference(unittest.TestCase):
    """
    Tests ability to infer class node
    and context from the given name
    """
    #Top level inferences. Easy cases
    def test_infer_class_simple(self):
        """Test ability to infer class defined in same series of statements"""

        class fixture():
            pass
        test = fixture()



