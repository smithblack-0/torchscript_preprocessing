import ast
import copy
import inspect
from dataclasses import dataclass
from typing import Any, List, Tuple, Dict, Type, Optional, Union, Callable
from copy import deepcopy

"""

Builders are part context, part helper. They 
are created when an appropriately named node
is identified during traversal, and act
to provide additional context to deeper nodes. 

Completely preprocessing a node consists
of going through all subnodes, attaching
the results to the created builder, 
and returning the results.



"""



#Order is important when editing here
#
#Note that it is the case that classes defined
#later in this source code have lower priority
#then those defined earlier.

class StackSupportNode():
    """
    A node in a support stack.

    This consists of various nodes
    linked together from the top
    level of the current
    file

    Following the parents of this
    will eventually reach the module
    at the top of the current context.

    Various subclasses take care of building the various
    node types.
    """
    registry: Dict[Type[ast.AST], Type["StackSupportNode"]] = {}
    @property
    def node(self) -> ast.AST:
        return self._node
    @classmethod
    def get_subclass(cls, node: Type[ast.AST])->Type["StackSupportNode"]:
        """Gets the approriate subclass"""
        return cls.registry[node]
    def push(self, node: ast.AST)->"StackSupportNode":
        """Push a new node onto the stack"""
        subclass = self.get_subclass(node.__class__)
        return subclass(node, self)
    def pop(self, node: ast.AST)->ast.AST:
        """Pops the current node off the stack. Returns the constructed ast node"""
        return self.construct()
    def construct(self)->ast.AST:
        """Constructs a new node from the current parameters"""
        raise NotImplementedError()
    def __init_subclass__(cls, typing: Type[ast.AST]):
        """Registers the subclass associated with the given ast node"""
        cls.registry[typing] = cls
    def __init__(self,
                 node: ast.AST,
                 parent: Optional["StackSupportNode"]
                 ):
        self.parent = parent
        self._node = node


