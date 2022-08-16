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


def infer_feature(node: StackSupportNode, name: str):
    """
    Attempt to infer any information possible about where
    and how the given node is defined

    :param node: The node to infer from
    :param name: The name of what to look for
    :return: A generator of options
    """
    def predicate(context: StackSupportNode, node: ast.AST)->bool:
        if not isinstance(node, ast.Name):
            return False
        if node.id != name:
            return False
        if not isinstance(node.ctx, ast.Store):
            return False
        return True

    for context, node in node.get_reverse_iterator():
        if not isinstance(node, ast.AST):
            continue
        context = context.push(node)
        captures = capture(node, predicate, context=context)
        for subcontext, subnode in captures:
            print(subcontext, subnode)
class modBuilderNode(StackSupportNode, typing=ast.mod):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    mod
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.mod:
        return self._node
    def __init__(self, node: ast.mod, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.mod:
        return ast.mod(
            
        )
    

class ModuleBuilderNode(StackSupportNode, typing=ast.Module):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Module
    """
    fields = ("body", "type_ignores", )
    annotations = (List[ast.stmt], List[ast.type_ignore], )
    @property
    def node(self)->ast.Module:
        return self._node
    def __init__(self, node: ast.Module, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.body: List[ast.stmt] = []
        self.type_ignores: List[ast.type_ignore] = []
    def construct(self)->ast.Module:
        return ast.Module(
            self.body,
            self.type_ignores,
        )
    

class InteractiveBuilderNode(StackSupportNode, typing=ast.Interactive):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Interactive
    """
    fields = ("body", )
    annotations = (List[ast.stmt], )
    @property
    def node(self)->ast.Interactive:
        return self._node
    def __init__(self, node: ast.Interactive, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.body: List[ast.stmt] = []
    def construct(self)->ast.Interactive:
        return ast.Interactive(
            self.body,
        )
    

class ExpressionBuilderNode(StackSupportNode, typing=ast.Expression):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Expression
    """
    fields = ("body", )
    annotations = (ast.expr, )
    @property
    def node(self)->ast.Expression:
        return self._node
    def __init__(self, node: ast.Expression, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.body: Optional[ast.expr] = None
    def construct(self)->ast.Expression:
        return ast.Expression(
            self.body,
        )
    

class FunctionTypeBuilderNode(StackSupportNode, typing=ast.FunctionType):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    FunctionType
    """
    fields = ("argtypes", "returns", )
    annotations = (List[ast.expr], ast.expr, )
    @property
    def node(self)->ast.FunctionType:
        return self._node
    def __init__(self, node: ast.FunctionType, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.argtypes: List[ast.expr] = []
        self.returns: Optional[ast.expr] = None
    def construct(self)->ast.FunctionType:
        return ast.FunctionType(
            self.argtypes,
            self.returns,
        )
    

class SuiteBuilderNode(StackSupportNode, typing=ast.Suite):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Suite
    """
    fields = ("body", )
    annotations = (List[ast.stmt], )
    @property
    def node(self)->ast.Suite:
        return self._node
    def __init__(self, node: ast.Suite, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.body: List[ast.stmt] = []
    def construct(self)->ast.Suite:
        return ast.Suite(
            self.body,
        )
    

class stmtBuilderNode(StackSupportNode, typing=ast.stmt):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    stmt
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.stmt:
        return self._node
    def __init__(self, node: ast.stmt, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.stmt:
        return ast.stmt(
            
        )
    

class FunctionDefBuilderNode(StackSupportNode, typing=ast.FunctionDef):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    FunctionDef
    """
    fields = ("name", "args", "body", "decorator_list", "returns", "type_comment", )
    annotations = (str, ast.arguments, List[ast.stmt], List[ast.expr], Optional[ast.expr], Optional[str], )
    @property
    def node(self)->ast.FunctionDef:
        return self._node
    def __init__(self, node: ast.FunctionDef, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.name: Optional[str] = None
        self.args: Optional[ast.arguments] = None
        self.body: List[ast.stmt] = []
        self.decorator_list: List[ast.expr] = []
        self.returns: Optional[Optional[ast.expr]] = None
        self.type_comment: Optional[Optional[str]] = None
    def construct(self)->ast.FunctionDef:
        return ast.FunctionDef(
            self.name,
            self.args,
            self.body,
            self.decorator_list,
            self.returns,
            self.type_comment,
        )
    

class AsyncFunctionDefBuilderNode(StackSupportNode, typing=ast.AsyncFunctionDef):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    AsyncFunctionDef
    """
    fields = ("name", "args", "body", "decorator_list", "returns", "type_comment", )
    annotations = (str, ast.arguments, List[ast.stmt], List[ast.expr], Optional[ast.expr], Optional[str], )
    @property
    def node(self)->ast.AsyncFunctionDef:
        return self._node
    def __init__(self, node: ast.AsyncFunctionDef, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.name: Optional[str] = None
        self.args: Optional[ast.arguments] = None
        self.body: List[ast.stmt] = []
        self.decorator_list: List[ast.expr] = []
        self.returns: Optional[Optional[ast.expr]] = None
        self.type_comment: Optional[Optional[str]] = None
    def construct(self)->ast.AsyncFunctionDef:
        return ast.AsyncFunctionDef(
            self.name,
            self.args,
            self.body,
            self.decorator_list,
            self.returns,
            self.type_comment,
        )
    

class ClassDefBuilderNode(StackSupportNode, typing=ast.ClassDef):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    ClassDef
    """
    fields = ("name", "bases", "keywords", "body", "decorator_list", )
    annotations = (str, List[ast.expr], List[ast.keyword], List[ast.stmt], List[ast.expr], )
    @property
    def node(self)->ast.ClassDef:
        return self._node
    def __init__(self, node: ast.ClassDef, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.name: Optional[str] = None
        self.bases: List[ast.expr] = []
        self.keywords: List[ast.keyword] = []
        self.body: List[ast.stmt] = []
        self.decorator_list: List[ast.expr] = []
    def construct(self)->ast.ClassDef:
        return ast.ClassDef(
            self.name,
            self.bases,
            self.keywords,
            self.body,
            self.decorator_list,
        )
    

class ReturnBuilderNode(StackSupportNode, typing=ast.Return):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Return
    """
    fields = ("value", )
    annotations = (Optional[ast.expr], )
    @property
    def node(self)->ast.Return:
        return self._node
    def __init__(self, node: ast.Return, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: Optional[Optional[ast.expr]] = None
    def construct(self)->ast.Return:
        return ast.Return(
            self.value,
        )
    

class DeleteBuilderNode(StackSupportNode, typing=ast.Delete):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Delete
    """
    fields = ("targets", )
    annotations = (List[ast.expr], )
    @property
    def node(self)->ast.Delete:
        return self._node
    def __init__(self, node: ast.Delete, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.targets: List[ast.expr] = []
    def construct(self)->ast.Delete:
        return ast.Delete(
            self.targets,
        )
    

class AssignBuilderNode(StackSupportNode, typing=ast.Assign):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Assign
    """
    fields = ("targets", "value", "type_comment", )
    annotations = (List[ast.expr], ast.expr, Optional[str], )
    @property
    def node(self)->ast.Assign:
        return self._node
    def __init__(self, node: ast.Assign, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.targets: List[ast.expr] = []
        self.value: Optional[ast.expr] = None
        self.type_comment: Optional[Optional[str]] = None
    def construct(self)->ast.Assign:
        return ast.Assign(
            self.targets,
            self.value,
            self.type_comment,
        )
    

class AugAssignBuilderNode(StackSupportNode, typing=ast.AugAssign):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    AugAssign
    """
    fields = ("target", "op", "value", )
    annotations = (ast.expr, ast.operator, ast.expr, )
    @property
    def node(self)->ast.AugAssign:
        return self._node
    def __init__(self, node: ast.AugAssign, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.target: Optional[ast.expr] = None
        self.op: Optional[ast.operator] = None
        self.value: Optional[ast.expr] = None
    def construct(self)->ast.AugAssign:
        return ast.AugAssign(
            self.target,
            self.op,
            self.value,
        )
    

class AnnAssignBuilderNode(StackSupportNode, typing=ast.AnnAssign):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    AnnAssign
    """
    fields = ("target", "annotation", "value", "simple", )
    annotations = (ast.expr, ast.expr, Optional[ast.expr], int, )
    @property
    def node(self)->ast.AnnAssign:
        return self._node
    def __init__(self, node: ast.AnnAssign, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.target: Optional[ast.expr] = None
        self.annotation: Optional[ast.expr] = None
        self.value: Optional[Optional[ast.expr]] = None
        self.simple: Optional[int] = None
    def construct(self)->ast.AnnAssign:
        return ast.AnnAssign(
            self.target,
            self.annotation,
            self.value,
            self.simple,
        )
    

class ForBuilderNode(StackSupportNode, typing=ast.For):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    For
    """
    fields = ("target", "iter", "body", "orelse", "type_comment", )
    annotations = (ast.expr, ast.expr, List[ast.stmt], List[ast.stmt], Optional[str], )
    @property
    def node(self)->ast.For:
        return self._node
    def __init__(self, node: ast.For, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.target: Optional[ast.expr] = None
        self.iter: Optional[ast.expr] = None
        self.body: List[ast.stmt] = []
        self.orelse: List[ast.stmt] = []
        self.type_comment: Optional[Optional[str]] = None
    def construct(self)->ast.For:
        return ast.For(
            self.target,
            self.iter,
            self.body,
            self.orelse,
            self.type_comment,
        )
    

class AsyncForBuilderNode(StackSupportNode, typing=ast.AsyncFor):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    AsyncFor
    """
    fields = ("target", "iter", "body", "orelse", "type_comment", )
    annotations = (ast.expr, ast.expr, List[ast.stmt], List[ast.stmt], Optional[str], )
    @property
    def node(self)->ast.AsyncFor:
        return self._node
    def __init__(self, node: ast.AsyncFor, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.target: Optional[ast.expr] = None
        self.iter: Optional[ast.expr] = None
        self.body: List[ast.stmt] = []
        self.orelse: List[ast.stmt] = []
        self.type_comment: Optional[Optional[str]] = None
    def construct(self)->ast.AsyncFor:
        return ast.AsyncFor(
            self.target,
            self.iter,
            self.body,
            self.orelse,
            self.type_comment,
        )
    

class WhileBuilderNode(StackSupportNode, typing=ast.While):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    While
    """
    fields = ("test", "body", "orelse", )
    annotations = (ast.expr, List[ast.stmt], List[ast.stmt], )
    @property
    def node(self)->ast.While:
        return self._node
    def __init__(self, node: ast.While, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.test: Optional[ast.expr] = None
        self.body: List[ast.stmt] = []
        self.orelse: List[ast.stmt] = []
    def construct(self)->ast.While:
        return ast.While(
            self.test,
            self.body,
            self.orelse,
        )
    

class IfBuilderNode(StackSupportNode, typing=ast.If):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    If
    """
    fields = ("test", "body", "orelse", )
    annotations = (ast.expr, List[ast.stmt], List[ast.stmt], )
    @property
    def node(self)->ast.If:
        return self._node
    def __init__(self, node: ast.If, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.test: Optional[ast.expr] = None
        self.body: List[ast.stmt] = []
        self.orelse: List[ast.stmt] = []
    def construct(self)->ast.If:
        return ast.If(
            self.test,
            self.body,
            self.orelse,
        )
    

class WithBuilderNode(StackSupportNode, typing=ast.With):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    With
    """
    fields = ("items", "body", "type_comment", )
    annotations = (List[ast.withitem], List[ast.stmt], Optional[str], )
    @property
    def node(self)->ast.With:
        return self._node
    def __init__(self, node: ast.With, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.items: List[ast.withitem] = []
        self.body: List[ast.stmt] = []
        self.type_comment: Optional[Optional[str]] = None
    def construct(self)->ast.With:
        return ast.With(
            self.items,
            self.body,
            self.type_comment,
        )
    

class AsyncWithBuilderNode(StackSupportNode, typing=ast.AsyncWith):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    AsyncWith
    """
    fields = ("items", "body", "type_comment", )
    annotations = (List[ast.withitem], List[ast.stmt], Optional[str], )
    @property
    def node(self)->ast.AsyncWith:
        return self._node
    def __init__(self, node: ast.AsyncWith, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.items: List[ast.withitem] = []
        self.body: List[ast.stmt] = []
        self.type_comment: Optional[Optional[str]] = None
    def construct(self)->ast.AsyncWith:
        return ast.AsyncWith(
            self.items,
            self.body,
            self.type_comment,
        )
    

class RaiseBuilderNode(StackSupportNode, typing=ast.Raise):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Raise
    """
    fields = ("exc", "cause", )
    annotations = (Optional[ast.expr], Optional[ast.expr], )
    @property
    def node(self)->ast.Raise:
        return self._node
    def __init__(self, node: ast.Raise, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.exc: Optional[Optional[ast.expr]] = None
        self.cause: Optional[Optional[ast.expr]] = None
    def construct(self)->ast.Raise:
        return ast.Raise(
            self.exc,
            self.cause,
        )
    

class TryBuilderNode(StackSupportNode, typing=ast.Try):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Try
    """
    fields = ("body", "handlers", "orelse", "finalbody", )
    annotations = (List[ast.stmt], List[ast.excepthandler], List[ast.stmt], List[ast.stmt], )
    @property
    def node(self)->ast.Try:
        return self._node
    def __init__(self, node: ast.Try, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.body: List[ast.stmt] = []
        self.handlers: List[ast.excepthandler] = []
        self.orelse: List[ast.stmt] = []
        self.finalbody: List[ast.stmt] = []
    def construct(self)->ast.Try:
        return ast.Try(
            self.body,
            self.handlers,
            self.orelse,
            self.finalbody,
        )
    

class AssertBuilderNode(StackSupportNode, typing=ast.Assert):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Assert
    """
    fields = ("test", "msg", )
    annotations = (ast.expr, Optional[ast.expr], )
    @property
    def node(self)->ast.Assert:
        return self._node
    def __init__(self, node: ast.Assert, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.test: Optional[ast.expr] = None
        self.msg: Optional[Optional[ast.expr]] = None
    def construct(self)->ast.Assert:
        return ast.Assert(
            self.test,
            self.msg,
        )
    

class ImportBuilderNode(StackSupportNode, typing=ast.Import):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Import
    """
    fields = ("names", )
    annotations = (List[ast.alias], )
    @property
    def node(self)->ast.Import:
        return self._node
    def __init__(self, node: ast.Import, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.names: List[ast.alias] = []
    def construct(self)->ast.Import:
        return ast.Import(
            self.names,
        )
    

class ImportFromBuilderNode(StackSupportNode, typing=ast.ImportFrom):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    ImportFrom
    """
    fields = ("module", "names", "level", )
    annotations = (Optional[str], List[ast.alias], Optional[int], )
    @property
    def node(self)->ast.ImportFrom:
        return self._node
    def __init__(self, node: ast.ImportFrom, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.module: Optional[Optional[str]] = None
        self.names: List[ast.alias] = []
        self.level: Optional[Optional[int]] = None
    def construct(self)->ast.ImportFrom:
        return ast.ImportFrom(
            self.module,
            self.names,
            self.level,
        )
    

class GlobalBuilderNode(StackSupportNode, typing=ast.Global):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Global
    """
    fields = ("names", )
    annotations = (List[str], )
    @property
    def node(self)->ast.Global:
        return self._node
    def __init__(self, node: ast.Global, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.names: List[str] = []
    def construct(self)->ast.Global:
        return ast.Global(
            self.names,
        )
    

class NonlocalBuilderNode(StackSupportNode, typing=ast.Nonlocal):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Nonlocal
    """
    fields = ("names", )
    annotations = (List[str], )
    @property
    def node(self)->ast.Nonlocal:
        return self._node
    def __init__(self, node: ast.Nonlocal, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.names: List[str] = []
    def construct(self)->ast.Nonlocal:
        return ast.Nonlocal(
            self.names,
        )
    

class ExprBuilderNode(StackSupportNode, typing=ast.Expr):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Expr
    """
    fields = ("value", )
    annotations = (ast.expr, )
    @property
    def node(self)->ast.Expr:
        return self._node
    def __init__(self, node: ast.Expr, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: Optional[ast.expr] = None
    def construct(self)->ast.Expr:
        return ast.Expr(
            self.value,
        )
    

class PassBuilderNode(StackSupportNode, typing=ast.Pass):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Pass
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Pass:
        return self._node
    def __init__(self, node: ast.Pass, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Pass:
        return ast.Pass(
            
        )
    

class BreakBuilderNode(StackSupportNode, typing=ast.Break):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Break
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Break:
        return self._node
    def __init__(self, node: ast.Break, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Break:
        return ast.Break(
            
        )
    

class ContinueBuilderNode(StackSupportNode, typing=ast.Continue):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Continue
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Continue:
        return self._node
    def __init__(self, node: ast.Continue, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Continue:
        return ast.Continue(
            
        )
    

class exprBuilderNode(StackSupportNode, typing=ast.expr):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    expr
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.expr:
        return self._node
    def __init__(self, node: ast.expr, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.expr:
        return ast.expr(
            
        )
    

class BoolOpBuilderNode(StackSupportNode, typing=ast.BoolOp):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    BoolOp
    """
    fields = ("op", "values", )
    annotations = (ast.boolop, List[ast.expr], )
    @property
    def node(self)->ast.BoolOp:
        return self._node
    def __init__(self, node: ast.BoolOp, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.op: Optional[ast.boolop] = None
        self.values: List[ast.expr] = []
    def construct(self)->ast.BoolOp:
        return ast.BoolOp(
            self.op,
            self.values,
        )
    

class NamedExprBuilderNode(StackSupportNode, typing=ast.NamedExpr):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    NamedExpr
    """
    fields = ("target", "value", )
    annotations = (ast.expr, ast.expr, )
    @property
    def node(self)->ast.NamedExpr:
        return self._node
    def __init__(self, node: ast.NamedExpr, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.target: Optional[ast.expr] = None
        self.value: Optional[ast.expr] = None
    def construct(self)->ast.NamedExpr:
        return ast.NamedExpr(
            self.target,
            self.value,
        )
    

class BinOpBuilderNode(StackSupportNode, typing=ast.BinOp):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    BinOp
    """
    fields = ("left", "op", "right", )
    annotations = (ast.expr, ast.operator, ast.expr, )
    @property
    def node(self)->ast.BinOp:
        return self._node
    def __init__(self, node: ast.BinOp, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.left: Optional[ast.expr] = None
        self.op: Optional[ast.operator] = None
        self.right: Optional[ast.expr] = None
    def construct(self)->ast.BinOp:
        return ast.BinOp(
            self.left,
            self.op,
            self.right,
        )
    

class UnaryOpBuilderNode(StackSupportNode, typing=ast.UnaryOp):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    UnaryOp
    """
    fields = ("op", "operand", )
    annotations = (ast.unaryop, ast.expr, )
    @property
    def node(self)->ast.UnaryOp:
        return self._node
    def __init__(self, node: ast.UnaryOp, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.op: Optional[ast.unaryop] = None
        self.operand: Optional[ast.expr] = None
    def construct(self)->ast.UnaryOp:
        return ast.UnaryOp(
            self.op,
            self.operand,
        )
    

class LambdaBuilderNode(StackSupportNode, typing=ast.Lambda):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Lambda
    """
    fields = ("args", "body", )
    annotations = (ast.arguments, ast.expr, )
    @property
    def node(self)->ast.Lambda:
        return self._node
    def __init__(self, node: ast.Lambda, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.args: Optional[ast.arguments] = None
        self.body: Optional[ast.expr] = None
    def construct(self)->ast.Lambda:
        return ast.Lambda(
            self.args,
            self.body,
        )
    

class IfExpBuilderNode(StackSupportNode, typing=ast.IfExp):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    IfExp
    """
    fields = ("test", "body", "orelse", )
    annotations = (ast.expr, ast.expr, ast.expr, )
    @property
    def node(self)->ast.IfExp:
        return self._node
    def __init__(self, node: ast.IfExp, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.test: Optional[ast.expr] = None
        self.body: Optional[ast.expr] = None
        self.orelse: Optional[ast.expr] = None
    def construct(self)->ast.IfExp:
        return ast.IfExp(
            self.test,
            self.body,
            self.orelse,
        )
    

class DictBuilderNode(StackSupportNode, typing=ast.Dict):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Dict
    """
    fields = ("keys", "values", )
    annotations = (List[ast.expr], List[ast.expr], )
    @property
    def node(self)->ast.Dict:
        return self._node
    def __init__(self, node: ast.Dict, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.keys: List[ast.expr] = []
        self.values: List[ast.expr] = []
    def construct(self)->ast.Dict:
        return ast.Dict(
            self.keys,
            self.values,
        )
    

class SetBuilderNode(StackSupportNode, typing=ast.Set):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Set
    """
    fields = ("elts", )
    annotations = (List[ast.expr], )
    @property
    def node(self)->ast.Set:
        return self._node
    def __init__(self, node: ast.Set, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.elts: List[ast.expr] = []
    def construct(self)->ast.Set:
        return ast.Set(
            self.elts,
        )
    

class ListCompBuilderNode(StackSupportNode, typing=ast.ListComp):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    ListComp
    """
    fields = ("elt", "generators", )
    annotations = (ast.expr, List[ast.comprehension], )
    @property
    def node(self)->ast.ListComp:
        return self._node
    def __init__(self, node: ast.ListComp, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.elt: Optional[ast.expr] = None
        self.generators: List[ast.comprehension] = []
    def construct(self)->ast.ListComp:
        return ast.ListComp(
            self.elt,
            self.generators,
        )
    

class SetCompBuilderNode(StackSupportNode, typing=ast.SetComp):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    SetComp
    """
    fields = ("elt", "generators", )
    annotations = (ast.expr, List[ast.comprehension], )
    @property
    def node(self)->ast.SetComp:
        return self._node
    def __init__(self, node: ast.SetComp, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.elt: Optional[ast.expr] = None
        self.generators: List[ast.comprehension] = []
    def construct(self)->ast.SetComp:
        return ast.SetComp(
            self.elt,
            self.generators,
        )
    

class DictCompBuilderNode(StackSupportNode, typing=ast.DictComp):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    DictComp
    """
    fields = ("key", "value", "generators", )
    annotations = (ast.expr, ast.expr, List[ast.comprehension], )
    @property
    def node(self)->ast.DictComp:
        return self._node
    def __init__(self, node: ast.DictComp, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.key: Optional[ast.expr] = None
        self.value: Optional[ast.expr] = None
        self.generators: List[ast.comprehension] = []
    def construct(self)->ast.DictComp:
        return ast.DictComp(
            self.key,
            self.value,
            self.generators,
        )
    

class GeneratorExpBuilderNode(StackSupportNode, typing=ast.GeneratorExp):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    GeneratorExp
    """
    fields = ("elt", "generators", )
    annotations = (ast.expr, List[ast.comprehension], )
    @property
    def node(self)->ast.GeneratorExp:
        return self._node
    def __init__(self, node: ast.GeneratorExp, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.elt: Optional[ast.expr] = None
        self.generators: List[ast.comprehension] = []
    def construct(self)->ast.GeneratorExp:
        return ast.GeneratorExp(
            self.elt,
            self.generators,
        )
    

class AwaitBuilderNode(StackSupportNode, typing=ast.Await):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Await
    """
    fields = ("value", )
    annotations = (ast.expr, )
    @property
    def node(self)->ast.Await:
        return self._node
    def __init__(self, node: ast.Await, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: Optional[ast.expr] = None
    def construct(self)->ast.Await:
        return ast.Await(
            self.value,
        )
    

class YieldBuilderNode(StackSupportNode, typing=ast.Yield):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Yield
    """
    fields = ("value", )
    annotations = (Optional[ast.expr], )
    @property
    def node(self)->ast.Yield:
        return self._node
    def __init__(self, node: ast.Yield, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: Optional[Optional[ast.expr]] = None
    def construct(self)->ast.Yield:
        return ast.Yield(
            self.value,
        )
    

class YieldFromBuilderNode(StackSupportNode, typing=ast.YieldFrom):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    YieldFrom
    """
    fields = ("value", )
    annotations = (ast.expr, )
    @property
    def node(self)->ast.YieldFrom:
        return self._node
    def __init__(self, node: ast.YieldFrom, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: Optional[ast.expr] = None
    def construct(self)->ast.YieldFrom:
        return ast.YieldFrom(
            self.value,
        )
    

class CompareBuilderNode(StackSupportNode, typing=ast.Compare):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Compare
    """
    fields = ("left", "ops", "comparators", )
    annotations = (ast.expr, List[ast.cmpop], List[ast.expr], )
    @property
    def node(self)->ast.Compare:
        return self._node
    def __init__(self, node: ast.Compare, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.left: Optional[ast.expr] = None
        self.ops: List[ast.cmpop] = []
        self.comparators: List[ast.expr] = []
    def construct(self)->ast.Compare:
        return ast.Compare(
            self.left,
            self.ops,
            self.comparators,
        )
    

class CallBuilderNode(StackSupportNode, typing=ast.Call):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Call
    """
    fields = ("func", "args", "keywords", )
    annotations = (ast.expr, List[ast.expr], List[ast.keyword], )
    @property
    def node(self)->ast.Call:
        return self._node
    def __init__(self, node: ast.Call, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.func: Optional[ast.expr] = None
        self.args: List[ast.expr] = []
        self.keywords: List[ast.keyword] = []
    def construct(self)->ast.Call:
        return ast.Call(
            self.func,
            self.args,
            self.keywords,
        )
    

class FormattedValueBuilderNode(StackSupportNode, typing=ast.FormattedValue):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    FormattedValue
    """
    fields = ("value", "conversion", "format_spec", )
    annotations = (ast.expr, Optional[int], Optional[ast.expr], )
    @property
    def node(self)->ast.FormattedValue:
        return self._node
    def __init__(self, node: ast.FormattedValue, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: Optional[ast.expr] = None
        self.conversion: Optional[Optional[int]] = None
        self.format_spec: Optional[Optional[ast.expr]] = None
    def construct(self)->ast.FormattedValue:
        return ast.FormattedValue(
            self.value,
            self.conversion,
            self.format_spec,
        )
    

class JoinedStrBuilderNode(StackSupportNode, typing=ast.JoinedStr):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    JoinedStr
    """
    fields = ("values", )
    annotations = (List[ast.expr], )
    @property
    def node(self)->ast.JoinedStr:
        return self._node
    def __init__(self, node: ast.JoinedStr, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.values: List[ast.expr] = []
    def construct(self)->ast.JoinedStr:
        return ast.JoinedStr(
            self.values,
        )
    

class ConstantBuilderNode(StackSupportNode, typing=ast.Constant):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Constant
    """
    fields = ("value", "kind", )
    annotations = (Union[str, int, float, complex, bool, None], Optional[str], )
    @property
    def node(self)->ast.Constant:
        return self._node
    def __init__(self, node: ast.Constant, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: Optional[Union[str, int, float, complex, bool, None]] = None
        self.kind: Optional[Optional[str]] = None
    def construct(self)->ast.Constant:
        return ast.Constant(
            self.value,
            self.kind,
        )
    

class AttributeBuilderNode(StackSupportNode, typing=ast.Attribute):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Attribute
    """
    fields = ("value", "attr", "ctx", )
    annotations = (ast.expr, str, ast.expr_context, )
    @property
    def node(self)->ast.Attribute:
        return self._node
    def __init__(self, node: ast.Attribute, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: Optional[ast.expr] = None
        self.attr: Optional[str] = None
        self.ctx: Optional[ast.expr_context] = None
    def construct(self)->ast.Attribute:
        return ast.Attribute(
            self.value,
            self.attr,
            self.ctx,
        )
    

class SubscriptBuilderNode(StackSupportNode, typing=ast.Subscript):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Subscript
    """
    fields = ("value", "slice", "ctx", )
    annotations = (ast.expr, ast.slice, ast.expr_context, )
    @property
    def node(self)->ast.Subscript:
        return self._node
    def __init__(self, node: ast.Subscript, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: Optional[ast.expr] = None
        self.slice: Optional[ast.slice] = None
        self.ctx: Optional[ast.expr_context] = None
    def construct(self)->ast.Subscript:
        return ast.Subscript(
            self.value,
            self.slice,
            self.ctx,
        )
    

class StarredBuilderNode(StackSupportNode, typing=ast.Starred):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Starred
    """
    fields = ("value", "ctx", )
    annotations = (ast.expr, ast.expr_context, )
    @property
    def node(self)->ast.Starred:
        return self._node
    def __init__(self, node: ast.Starred, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: Optional[ast.expr] = None
        self.ctx: Optional[ast.expr_context] = None
    def construct(self)->ast.Starred:
        return ast.Starred(
            self.value,
            self.ctx,
        )
    

class NameBuilderNode(StackSupportNode, typing=ast.Name):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Name
    """
    fields = ("id", "ctx", )
    annotations = (str, ast.expr_context, )
    @property
    def node(self)->ast.Name:
        return self._node
    def __init__(self, node: ast.Name, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.id: Optional[str] = None
        self.ctx: Optional[ast.expr_context] = None
    def construct(self)->ast.Name:
        return ast.Name(
            self.id,
            self.ctx,
        )
    

class ListBuilderNode(StackSupportNode, typing=ast.List):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    List
    """
    fields = ("elts", "ctx", )
    annotations = (List[ast.expr], ast.expr_context, )
    @property
    def node(self)->ast.List:
        return self._node
    def __init__(self, node: ast.List, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.elts: List[ast.expr] = []
        self.ctx: Optional[ast.expr_context] = None
    def construct(self)->ast.List:
        return ast.List(
            self.elts,
            self.ctx,
        )
    

class TupleBuilderNode(StackSupportNode, typing=ast.Tuple):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Tuple
    """
    fields = ("elts", "ctx", )
    annotations = (List[ast.expr], ast.expr_context, )
    @property
    def node(self)->ast.Tuple:
        return self._node
    def __init__(self, node: ast.Tuple, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.elts: List[ast.expr] = []
        self.ctx: Optional[ast.expr_context] = None
    def construct(self)->ast.Tuple:
        return ast.Tuple(
            self.elts,
            self.ctx,
        )
    

class expr_contextBuilderNode(StackSupportNode, typing=ast.expr_context):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    expr_context
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.expr_context:
        return self._node
    def __init__(self, node: ast.expr_context, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.expr_context:
        return ast.expr_context(
            
        )
    

class LoadBuilderNode(StackSupportNode, typing=ast.Load):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Load
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Load:
        return self._node
    def __init__(self, node: ast.Load, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Load:
        return ast.Load(
            
        )
    

class StoreBuilderNode(StackSupportNode, typing=ast.Store):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Store
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Store:
        return self._node
    def __init__(self, node: ast.Store, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Store:
        return ast.Store(
            
        )
    

class DelBuilderNode(StackSupportNode, typing=ast.Del):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Del
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Del:
        return self._node
    def __init__(self, node: ast.Del, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Del:
        return ast.Del(
            
        )
    

class AugLoadBuilderNode(StackSupportNode, typing=ast.AugLoad):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    AugLoad
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.AugLoad:
        return self._node
    def __init__(self, node: ast.AugLoad, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.AugLoad:
        return ast.AugLoad(
            
        )
    

class AugStoreBuilderNode(StackSupportNode, typing=ast.AugStore):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    AugStore
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.AugStore:
        return self._node
    def __init__(self, node: ast.AugStore, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.AugStore:
        return ast.AugStore(
            
        )
    

class ParamBuilderNode(StackSupportNode, typing=ast.Param):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Param
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Param:
        return self._node
    def __init__(self, node: ast.Param, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Param:
        return ast.Param(
            
        )
    

class sliceBuilderNode(StackSupportNode, typing=ast.slice):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    slice
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.slice:
        return self._node
    def __init__(self, node: ast.slice, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.slice:
        return ast.slice(
            
        )
    

class SliceBuilderNode(StackSupportNode, typing=ast.Slice):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Slice
    """
    fields = ("lower", "upper", "step", )
    annotations = (Optional[ast.expr], Optional[ast.expr], Optional[ast.expr], )
    @property
    def node(self)->ast.Slice:
        return self._node
    def __init__(self, node: ast.Slice, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.lower: Optional[Optional[ast.expr]] = None
        self.upper: Optional[Optional[ast.expr]] = None
        self.step: Optional[Optional[ast.expr]] = None
    def construct(self)->ast.Slice:
        return ast.Slice(
            self.lower,
            self.upper,
            self.step,
        )
    

class ExtSliceBuilderNode(StackSupportNode, typing=ast.ExtSlice):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    ExtSlice
    """
    fields = ("dims", )
    annotations = (List[ast.slice], )
    @property
    def node(self)->ast.ExtSlice:
        return self._node
    def __init__(self, node: ast.ExtSlice, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.dims: List[ast.slice] = []
    def construct(self)->ast.ExtSlice:
        return ast.ExtSlice(
            self.dims,
        )
    

class IndexBuilderNode(StackSupportNode, typing=ast.Index):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Index
    """
    fields = ("value", )
    annotations = (ast.expr, )
    @property
    def node(self)->ast.Index:
        return self._node
    def __init__(self, node: ast.Index, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: Optional[ast.expr] = None
    def construct(self)->ast.Index:
        return ast.Index(
            self.value,
        )
    

class boolopBuilderNode(StackSupportNode, typing=ast.boolop):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    boolop
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.boolop:
        return self._node
    def __init__(self, node: ast.boolop, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.boolop:
        return ast.boolop(
            
        )
    

class AndBuilderNode(StackSupportNode, typing=ast.And):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    And
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.And:
        return self._node
    def __init__(self, node: ast.And, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.And:
        return ast.And(
            
        )
    

class OrBuilderNode(StackSupportNode, typing=ast.Or):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Or
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Or:
        return self._node
    def __init__(self, node: ast.Or, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Or:
        return ast.Or(
            
        )
    

class operatorBuilderNode(StackSupportNode, typing=ast.operator):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    operator
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.operator:
        return self._node
    def __init__(self, node: ast.operator, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.operator:
        return ast.operator(
            
        )
    

class AddBuilderNode(StackSupportNode, typing=ast.Add):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Add
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Add:
        return self._node
    def __init__(self, node: ast.Add, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Add:
        return ast.Add(
            
        )
    

class SubBuilderNode(StackSupportNode, typing=ast.Sub):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Sub
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Sub:
        return self._node
    def __init__(self, node: ast.Sub, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Sub:
        return ast.Sub(
            
        )
    

class MultBuilderNode(StackSupportNode, typing=ast.Mult):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Mult
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Mult:
        return self._node
    def __init__(self, node: ast.Mult, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Mult:
        return ast.Mult(
            
        )
    

class MatMultBuilderNode(StackSupportNode, typing=ast.MatMult):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    MatMult
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.MatMult:
        return self._node
    def __init__(self, node: ast.MatMult, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.MatMult:
        return ast.MatMult(
            
        )
    

class DivBuilderNode(StackSupportNode, typing=ast.Div):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Div
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Div:
        return self._node
    def __init__(self, node: ast.Div, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Div:
        return ast.Div(
            
        )
    

class ModBuilderNode(StackSupportNode, typing=ast.Mod):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Mod
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Mod:
        return self._node
    def __init__(self, node: ast.Mod, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Mod:
        return ast.Mod(
            
        )
    

class PowBuilderNode(StackSupportNode, typing=ast.Pow):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Pow
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Pow:
        return self._node
    def __init__(self, node: ast.Pow, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Pow:
        return ast.Pow(
            
        )
    

class LShiftBuilderNode(StackSupportNode, typing=ast.LShift):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    LShift
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.LShift:
        return self._node
    def __init__(self, node: ast.LShift, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.LShift:
        return ast.LShift(
            
        )
    

class RShiftBuilderNode(StackSupportNode, typing=ast.RShift):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    RShift
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.RShift:
        return self._node
    def __init__(self, node: ast.RShift, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.RShift:
        return ast.RShift(
            
        )
    

class BitOrBuilderNode(StackSupportNode, typing=ast.BitOr):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    BitOr
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.BitOr:
        return self._node
    def __init__(self, node: ast.BitOr, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.BitOr:
        return ast.BitOr(
            
        )
    

class BitXorBuilderNode(StackSupportNode, typing=ast.BitXor):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    BitXor
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.BitXor:
        return self._node
    def __init__(self, node: ast.BitXor, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.BitXor:
        return ast.BitXor(
            
        )
    

class BitAndBuilderNode(StackSupportNode, typing=ast.BitAnd):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    BitAnd
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.BitAnd:
        return self._node
    def __init__(self, node: ast.BitAnd, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.BitAnd:
        return ast.BitAnd(
            
        )
    

class FloorDivBuilderNode(StackSupportNode, typing=ast.FloorDiv):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    FloorDiv
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.FloorDiv:
        return self._node
    def __init__(self, node: ast.FloorDiv, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.FloorDiv:
        return ast.FloorDiv(
            
        )
    

class unaryopBuilderNode(StackSupportNode, typing=ast.unaryop):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    unaryop
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.unaryop:
        return self._node
    def __init__(self, node: ast.unaryop, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.unaryop:
        return ast.unaryop(
            
        )
    

class InvertBuilderNode(StackSupportNode, typing=ast.Invert):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Invert
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Invert:
        return self._node
    def __init__(self, node: ast.Invert, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Invert:
        return ast.Invert(
            
        )
    

class NotBuilderNode(StackSupportNode, typing=ast.Not):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Not
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Not:
        return self._node
    def __init__(self, node: ast.Not, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Not:
        return ast.Not(
            
        )
    

class UAddBuilderNode(StackSupportNode, typing=ast.UAdd):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    UAdd
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.UAdd:
        return self._node
    def __init__(self, node: ast.UAdd, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.UAdd:
        return ast.UAdd(
            
        )
    

class USubBuilderNode(StackSupportNode, typing=ast.USub):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    USub
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.USub:
        return self._node
    def __init__(self, node: ast.USub, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.USub:
        return ast.USub(
            
        )
    

class cmpopBuilderNode(StackSupportNode, typing=ast.cmpop):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    cmpop
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.cmpop:
        return self._node
    def __init__(self, node: ast.cmpop, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.cmpop:
        return ast.cmpop(
            
        )
    

class EqBuilderNode(StackSupportNode, typing=ast.Eq):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Eq
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Eq:
        return self._node
    def __init__(self, node: ast.Eq, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Eq:
        return ast.Eq(
            
        )
    

class NotEqBuilderNode(StackSupportNode, typing=ast.NotEq):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    NotEq
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.NotEq:
        return self._node
    def __init__(self, node: ast.NotEq, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.NotEq:
        return ast.NotEq(
            
        )
    

class LtBuilderNode(StackSupportNode, typing=ast.Lt):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Lt
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Lt:
        return self._node
    def __init__(self, node: ast.Lt, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Lt:
        return ast.Lt(
            
        )
    

class LtEBuilderNode(StackSupportNode, typing=ast.LtE):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    LtE
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.LtE:
        return self._node
    def __init__(self, node: ast.LtE, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.LtE:
        return ast.LtE(
            
        )
    

class GtBuilderNode(StackSupportNode, typing=ast.Gt):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Gt
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Gt:
        return self._node
    def __init__(self, node: ast.Gt, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Gt:
        return ast.Gt(
            
        )
    

class GtEBuilderNode(StackSupportNode, typing=ast.GtE):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    GtE
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.GtE:
        return self._node
    def __init__(self, node: ast.GtE, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.GtE:
        return ast.GtE(
            
        )
    

class IsBuilderNode(StackSupportNode, typing=ast.Is):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    Is
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.Is:
        return self._node
    def __init__(self, node: ast.Is, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Is:
        return ast.Is(
            
        )
    

class IsNotBuilderNode(StackSupportNode, typing=ast.IsNot):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    IsNot
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.IsNot:
        return self._node
    def __init__(self, node: ast.IsNot, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.IsNot:
        return ast.IsNot(
            
        )
    

class InBuilderNode(StackSupportNode, typing=ast.In):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    In
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.In:
        return self._node
    def __init__(self, node: ast.In, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.In:
        return ast.In(
            
        )
    

class NotInBuilderNode(StackSupportNode, typing=ast.NotIn):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    NotIn
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.NotIn:
        return self._node
    def __init__(self, node: ast.NotIn, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.NotIn:
        return ast.NotIn(
            
        )
    

class comprehensionBuilderNode(StackSupportNode, typing=ast.comprehension):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    comprehension
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.comprehension:
        return self._node
    def __init__(self, node: ast.comprehension, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.comprehension:
        return ast.comprehension(
            
        )
    

class comprehensionBuilderNode(StackSupportNode, typing=ast.comprehension):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    comprehension
    """
    fields = ("target", "iter", "ifs", "is_async", )
    annotations = (ast.expr, ast.expr, List[ast.expr], int, )
    @property
    def node(self)->ast.comprehension:
        return self._node
    def __init__(self, node: ast.comprehension, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.target: Optional[ast.expr] = None
        self.iter: Optional[ast.expr] = None
        self.ifs: List[ast.expr] = []
        self.is_async: Optional[int] = None
    def construct(self)->ast.comprehension:
        return ast.comprehension(
            self.target,
            self.iter,
            self.ifs,
            self.is_async,
        )
    

class excepthandlerBuilderNode(StackSupportNode, typing=ast.excepthandler):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    excepthandler
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.excepthandler:
        return self._node
    def __init__(self, node: ast.excepthandler, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.excepthandler:
        return ast.excepthandler(
            
        )
    

class ExceptHandlerBuilderNode(StackSupportNode, typing=ast.ExceptHandler):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    ExceptHandler
    """
    fields = ("type", "name", "body", )
    annotations = (Optional[ast.expr], Optional[str], List[ast.stmt], )
    @property
    def node(self)->ast.ExceptHandler:
        return self._node
    def __init__(self, node: ast.ExceptHandler, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.type: Optional[Optional[ast.expr]] = None
        self.name: Optional[Optional[str]] = None
        self.body: List[ast.stmt] = []
    def construct(self)->ast.ExceptHandler:
        return ast.ExceptHandler(
            self.type,
            self.name,
            self.body,
        )
    

class argumentsBuilderNode(StackSupportNode, typing=ast.arguments):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    arguments
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.arguments:
        return self._node
    def __init__(self, node: ast.arguments, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.arguments:
        return ast.arguments(
            
        )
    

class argumentsBuilderNode(StackSupportNode, typing=ast.arguments):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    arguments
    """
    fields = ("posonlyargs", "args", "vararg", "kwonlyargs", "kw_defaults", "kwarg", "defaults", )
    annotations = (List[ast.arg], List[ast.arg], Optional[ast.arg], List[ast.arg], List[ast.expr], Optional[ast.arg], List[ast.expr], )
    @property
    def node(self)->ast.arguments:
        return self._node
    def __init__(self, node: ast.arguments, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.posonlyargs: List[ast.arg] = []
        self.args: List[ast.arg] = []
        self.vararg: Optional[Optional[ast.arg]] = None
        self.kwonlyargs: List[ast.arg] = []
        self.kw_defaults: List[ast.expr] = []
        self.kwarg: Optional[Optional[ast.arg]] = None
        self.defaults: List[ast.expr] = []
    def construct(self)->ast.arguments:
        return ast.arguments(
            self.posonlyargs,
            self.args,
            self.vararg,
            self.kwonlyargs,
            self.kw_defaults,
            self.kwarg,
            self.defaults,
        )
    

class argBuilderNode(StackSupportNode, typing=ast.arg):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    arg
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.arg:
        return self._node
    def __init__(self, node: ast.arg, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.arg:
        return ast.arg(
            
        )
    

class argBuilderNode(StackSupportNode, typing=ast.arg):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    arg
    """
    fields = ("arg", "annotation", "type_comment", )
    annotations = (str, Optional[ast.expr], Optional[str], )
    @property
    def node(self)->ast.arg:
        return self._node
    def __init__(self, node: ast.arg, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.arg: Optional[str] = None
        self.annotation: Optional[Optional[ast.expr]] = None
        self.type_comment: Optional[Optional[str]] = None
    def construct(self)->ast.arg:
        return ast.arg(
            self.arg,
            self.annotation,
            self.type_comment,
        )
    

class keywordBuilderNode(StackSupportNode, typing=ast.keyword):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    keyword
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.keyword:
        return self._node
    def __init__(self, node: ast.keyword, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.keyword:
        return ast.keyword(
            
        )
    

class keywordBuilderNode(StackSupportNode, typing=ast.keyword):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    keyword
    """
    fields = ("arg", "value", )
    annotations = (Optional[str], ast.expr, )
    @property
    def node(self)->ast.keyword:
        return self._node
    def __init__(self, node: ast.keyword, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.arg: Optional[Optional[str]] = None
        self.value: Optional[ast.expr] = None
    def construct(self)->ast.keyword:
        return ast.keyword(
            self.arg,
            self.value,
        )
    

class aliasBuilderNode(StackSupportNode, typing=ast.alias):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    alias
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.alias:
        return self._node
    def __init__(self, node: ast.alias, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.alias:
        return ast.alias(
            
        )
    

class aliasBuilderNode(StackSupportNode, typing=ast.alias):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    alias
    """
    fields = ("name", "asname", )
    annotations = (str, Optional[str], )
    @property
    def node(self)->ast.alias:
        return self._node
    def __init__(self, node: ast.alias, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.name: Optional[str] = None
        self.asname: Optional[Optional[str]] = None
    def construct(self)->ast.alias:
        return ast.alias(
            self.name,
            self.asname,
        )
    

class withitemBuilderNode(StackSupportNode, typing=ast.withitem):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    withitem
    """
    fields = ()
    annotations = ()
    @property
    def node(self)->ast.withitem:
        return self._node
    def __init__(self, node: ast.withitem, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.withitem:
        return ast.withitem(
            
        )
    

class withitemBuilderNode(StackSupportNode, typing=ast.withitem):
    """
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    withitem
    """
    fields = ("context_expr", "optional_vars", )
    annotations = (ast.expr, Optional[ast.expr], )
    @property
    def node(self)->ast.withitem:
        return self._node
    def __init__(self, node: ast.withitem, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.context_expr: Optional[ast.expr] = None
        self.optional_vars: Optional[Optional[ast.expr]] = None
    def construct(self)->ast.withitem:
        return ast.withitem(
            self.context_expr,
            self.optional_vars,
        )
    
