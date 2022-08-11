"""
The main module for preprocessing


"""
import ast
import inspect
from enum import Enum
from typing import Any



def parentize(tree: ast.AST):
    """Attach parent information onto an ast tree"""
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node
    return tree

class AbstractTransform():
    """ A base transform."""


class MRO_Transformer(AbstractTransform):
    """
    A rewriter for inheritance and other MRO effects. Responsible for
    detecting and executing an inheritance rewrite.
    """
    @staticmethod
    def detect_inheritance(node: ast.AST)->bool:
        """ Detects whether a particular ast node is an inheriting class"""
        raise NotImplementedError()
    @staticmethod
    def rewrite_inheritance(rewrite_stream, node: ast.ClassDef)->ast.ClassDef:
        """Rewrites inheritance with override analysis"""
        raise NotImplementedError()

class ClassAttributeTransformer(AbstractTransform):
    """
    A rewriter for handling class attributes.
    """
    @staticmethod
    def detect(node: ast.AST)->bool:
        raise NotImplementedError()
    @staticmethod
    def rewrite(stream, node: ast.ClassDef)->ast.ClassDef:
        raise NotImplementedError()

class InlineClassTransformer():
    """
    A rewriter to handle inline class definitions.
    """
    @staticmethod
    def detect(node: ast.AST)->bool:
        raise NotImplementedError()
    @staticmethod
    def rewrite(stream, node: ast.ClassDef)->ast.Call:
        raise NotImplementedError()

class InlineFunctionTransformer():
    """
    A preprocessor to handle inline function definitions
    """
    @staticmethod
    def detect(node: ast.AST):
        raise NotImplementedError()
    @staticmethod
    def rewrite(stream, node: ast.FunctionDef)->ast.Call:


source = inspect.getsource(test)
tree = ast.parse(source)
tree = parentize(tree)
print(tree.body[0].parent)