import builder
import ast
from typing import List, Dict, Tuple, Type, Callable


class Reformatter():
    """
    A class with methods for reformatting.

    It may be assumed that by the time this
    class is coming into play, a depth
    first compilation has occurred and
    any problem with child nodes is already resolved.
    """
    @staticmethod
    def is_match(context: builder.StackSupportNode, node: ast.AST)->bool:
        raise NotImplementedError("Must impliment is match")
    @staticmethod
    def refactor(context: builder.StackSupportNode, node, compiler):
        raise NotImplementedError("Must impliment refactor")

class Inheritance(Reformatter):
    """
    Detects and reformats inheriting nodes
    for functional independence.
    """
    @staticmethod
    def is_match(context: builder.StackSupportNode, node: ast.AST) ->bool:
        if isinstance(node, ast.ClassDef) and len(node.bases) > 0:
            return True
        return False
    @staticmethod
    def refactor(context: builder.StackSupportNode, node, compiler: Callable):
        #Perform static analysis on the class. Then transfer
        #all inherited class features over.



        for context, node in