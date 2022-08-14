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
    fields = ()
    annotations = ()
    @property
    def node(self) -> ast.AST:
        return self._node
    @property
    def is_root(self):
        if self._node is None:
            return True
        return False
    @classmethod
    def get_subclass(cls, node: Type[ast.AST])->Type["StackSupportNode"]:
        """Gets the approriate subclass"""
        return cls.registry[node]
    def push(self, node: Union[ast.AST, List[ast.AST]])->"StackSupportNode":
        """Push a new node onto the stack"""
        subclass = self.get_subclass(node.__class__)
        if self.parent is None:
            return subclass(node, self)
        else:
            for field, typing in zip(self.fields, self.annotations):
                if getattr(self, field) is node:
                    return subclass(node, self, typing)
            raise ValueError("Attempt to push node not on ast feature.")
    def pop(self)->ast.AST:
        """Pops the current node off the stack. Returns the constructed ast node"""
        return self.construct()
    def construct(self)->ast.AST:
        """Constructs a new node from the current parameters"""
        raise NotImplementedError()
    def __init_subclass__(cls, typing: Type[ast.AST]):
        """Registers the subclass associated with the given ast node"""
        cls.registry[typing] = cls
    def __init__(self,
                 node: Optional[Union[ast.AST, List[ast.AST]]]=None,
                 parent: Optional["StackSupportNode"] = None,
                 auxilary: Optional[Type] = None
                 ):
        self.parent = parent
        self._node = node

class listSupportNode(StackSupportNode, typing=list):
    """
    A node for generating list features. Some
    features of an ast node will be a list, which
    must later be compiled into some sort of
    reasonable statement.

    This will then promise to handle any requests
    for these kinds of nodes.
    """
    def __init__(self, node: list, parent: StackSupportNode, auxilary: str):
        """Creates the build list."""
        super().__init__(node, parent)
        self.type = auxilary
        self.list: List["StackSupportNode"] = []
    def construct(self) -> List["StackSupportNode"]:
        output = []
        for item in self.list:
            if item is None:
                continue
            elif isinstance(item, self.type):
                output.append(item)
            else:
                raise ValueError("Item %s is not of type %s" % (item, self.type))
        return output

