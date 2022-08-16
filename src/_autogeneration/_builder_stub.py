import ast
import copy
import inspect
from dataclasses import dataclass
import typing as typing_std_lib #I had already used typing in code.
from typing import Any, List, Tuple, Dict, Type, Optional, Union, Callable, Generator
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
    registry: Dict[Type, Type["StackSupportNode"]] = {}
    fields = ()
    annotations = ()
    @property
    def node(self) -> ast.AST:
        return self._node
    @property
    def is_root(self)->bool:
        if self._node is None:
            return True
        return False
    @property
    def root(self)->"StackSupportNode":
        if self.parent is None:
            return self
        return self.parent.root()
    @classmethod
    def get_subclass(cls, node: Type[ast.AST])->Type["StackSupportNode"]:
        """Gets the approriate subclass"""
        return cls.registry[node]
    def push(self, node: Union[ast.AST, List[ast.AST]])->"StackSupportNode":
        """Push a new node onto the stack"""
        subclass = self.get_subclass(node.__class__)
        return subclass(node, self)
    def pop(self)->ast.AST:
        """Pops the current node off the stack. Returns the constructed ast node"""
        return self.construct()
    def construct(self)->ast.AST:
        """Constructs a new node from the current parameters"""
        raise NotImplementedError()
    def place(self, fieldname: str, value: Any):
        """Places the given value into the given fieldname. Lists are appended to. Raw slots are replaced"""
        if isinstance(getattr(self, fieldname), list):
            getattr(self, fieldname).append(value)
        else:
            assert getattr(self, fieldname) is None, "Attribute of name %s already set" % fieldname
            setattr(self, fieldname, value)
    def get_pos(self, target_child: ast.AST)->Tuple[str, Optional[int]]:
        """Gets the position of the indicated ast child
            node
        """
        #Get the correct field
        final_field_name = None
        child = None
        for fieldname, child in self.get_child_iterator():
            if target_child is child:
                final_field_name = fieldname
                break
        if final_field_name is None:
            raise KeyError("Child not on node")

        #Return the correct type
        if isinstance(getattr(self, final_field_name), list):
            return final_field_name, getattr(self, fieldname).index(child)
        else:
            return final_field_name, None

    def get_child_iterator(self)->Generator[Tuple[str, Any], None, None]:
        """
        Iterates over every node directly attached
        to the ast node. Notably, indicates the
        field we are currently working in.
        """
        for fieldname, value in ast.iter_fields(self.node):
            if isinstance(value, list):
                for subitem in value:
                    yield fieldname, subitem
            else:
                yield fieldname, value

    def get_ancestor_iterator(self):
        """Starting with self, yields the entries seen going up the ancestor chain"""
        parent = self.parent
        yield self
        while parent is not None:
            yield parent
            parent = parent.parent

    def get_reverse_iterator(self)->Generator[Tuple["StackSupportNode", ast.AST], None, None]:
        """A reverse iterator. Iterates backwards from self to parent"""
        #Basically, this gets the forward sequence as a list,
        #then just reverses and yields the result.
        #
        #Then it yields the result seen from moving up the stack.

        if self.parent.node is not None:
            nodes = []
            for fieldname, node in self.parent.get_child_iterator():
                if node is self.node:
                    break
                else:
                    nodes.append(node)

            nodes.reverse()
            for node in nodes:
                yield self.parent, node
            for node in self.parent.get_reverse_iterator():
                yield node


    def __init_subclass__(cls, typing: Type):
        """Registers the subclass associated with the given ast node"""
        if typing_std_lib.get_origin(typing) is Union:
            #Get union arguments then store each one in association
            args = typing_std_lib.get_args(typing)
        else:
            args = [typing]
        for arg in args:
            cls.registry[arg] = cls

    def __init__(self,
                 node: Optional[Union[ast.AST, List[ast.AST]]]=None,
                 parent: Optional["StackSupportNode"] = None,
                 ):
        self.parent = parent
        self._node = node


def rebuild(node: ast.AST,
            transformer: Callable[[StackSupportNode, ast.AST], StackSupportNode],
            context: Optional[StackSupportNode] = None,
            ) -> ast.AST:
    """
    A walker for working with an ast tree and autogenerating context.
    This is designed to assist with creating a new node.

    The transformer is called right before a particular stacknode
    is turned back into an ast ndoe.

    :param node: an ast tree to start at.
    :param predicate: A predicate to match on. Will present a context, and the node
    :param helper: An optional feature, showing the existing context
    :return:  A tuple of the context, and the ast node.
    """
    if context is None:
        context = StackSupportNode()
    context = context.push(node)
    stack = []
    generator = context.get_child_iterator()
    while True:
        try:
            fieldname, child = next(generator)
            if isinstance(child, ast.AST):
                stack.append((fieldname, child, generator, context))
                context = context.push(child)
                generator = context.get_child_iterator()
            else:
                context.place(fieldname, child)
        except StopIteration:
            if len(stack) == 0:
                break
            #Working on the child node
            node = context.pop() #Preliminary, indicating what has happened so far
            context = transformer(context, node)
            node_update = context.pop() #Final

            #Parent node. Ascending stack
            fieldname, child, generator, context = stack.pop()
            context.place(fieldname, node_update)
    return context.pop()


def capture(node: ast.AST,
         predicate: Callable[[StackSupportNode, ast.AST], bool],
         context: Optional[StackSupportNode]=None,
         stop: Optional[Callable[[StackSupportNode, ast.AST], bool]] = None
         )->Generator[Tuple[StackSupportNode, ast.AST], None, None]:
    """
    A walker for working with an ast tree and autogenerating context.
    This will walk all the children in the tree, returning nodes
    as we go. It will only yield nodes matching the predicate.

    :param node: an ast tree to start at.
    :param predicate: A predicate to match on. Will present a context, and the node
    :param helper: An optional feature, showing the existing context
    :return:  A tuple of the context, and the ast node.
    """
    if context is None:
        context = StackSupportNode()
    context = context.push(node)
    stack = []
    generator = context.get_child_iterator()
    while True:
        try:
            fieldname, child = next(generator)
            if isinstance(child, ast.AST):
                stack.append((child, generator, context))
                context = context.push(child)
                generator = context.get_child_iterator()
        except StopIteration:
            if len(stack) == 0:
                break
            child, generator, context = stack.pop()
            if stop is not None and stop(context, child):
                break
            if predicate(context, child):
                yield context, child




