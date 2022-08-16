
from typing import List, Dict, Tuple
import unittest
import inspect
import ast
import warnings
import astunparse
from src import builder
from typing import Optional

testretrieval2 = 6

class test_utility_functions(unittest.TestCase):
    test_retrieval = 5
    def test_rebuild_source(self):
        """ Tests that rebuild can recreate source"""
        source = inspect.getsource(test_utility_functions)
        tree = ast.parse(source)
        def transform(context, node):
            return context

        new_tree = builder.rebuild(tree, transform)
        old_nodes = list(ast.walk(tree))
        new_nodes = list(ast.walk(tree))
        self.assertTrue(len(old_nodes)==len(new_nodes))
        for old, new in zip(old_nodes, new_nodes):
            self.assertTrue(type(old) == type(new))
    def test_rebuild_replace(self):
        """test that replacement is meaningful"""
        source = inspect.getsource(test_utility_functions)
        tree = ast.parse(source)
        def transform(context, node):
            if isinstance(node, ast.FunctionDef):
                context.body = []
            return context
        new_tree = builder.rebuild(tree, transform)
        for node in ast.walk(new_tree):
            if isinstance(node, ast.FunctionDef):
                self.assertTrue(len(node.body) == 0)
    def test_reverse_iterator(self):
        source = inspect.getsource(test_utility_functions)
        tree = ast.parse(source)
        captures = builder.capture(tree, lambda context, node : isinstance(node, ast.FunctionDef))
        for context, node in captures:
            for context, subnode in context.get_reverse_iterator():
                #TODO: Make a little more rigorous
                pass
        warnings.warn("Warning, reverse iterator test not thorough enough")
