"""


The preprocessing algorithm consists of generating a stack of
important modification handles which can and must be utilized
to produce sane results.

"""
import ast
import astunparse
import inspect
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Tuple, Dict




import ast
from typing import List

from builder import NodeBuilder


class StackSupport:
    """
    A context manager for the ast tree.

    Knows what is going on, and how deep the stack currently
    is into the tree.
    """

    def __init__(self, obj: object):
        """
        We need to go get the rest of the tree as
        available features. To do this,simply we go ahead
        and parse the entire module, then chase
        down where we currently are in the tree

        :param obj: The object to get source from
        """

        #Get target source data
        source = inspect.getsource(obj)
        source = ast.parse(source)
        source = ast.unparse(source)

        #Get the entire module tree.
        module = inspect.getmodule(obj)
        lines, no = inspect.getsourcelines(module)
        module_source = "\n".join(lines)
        module_source = ast.parse(module_source)

        #Walk the tree, search for the proper condition

    def push(self, node: ast.AST):
        """Push a new feature onto the stack"""
        self.stack.append(NodeBuilder(node))

    def pop(self) -> ast.AST:
        """Pop a node back off of the stack"""
        builder = self.stack.pop()
        return builder.finish()


def CaseRegistry():
    """A registry keeping track of the various trans"""