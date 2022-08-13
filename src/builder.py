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




class modBuilderNode(StackSupportNode, typing=ast.mod):
    """
    This is a node to support the 
    creation of ast nodes of variety
    mod
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    Module
    """
    @property
    def node(self)->ast.Module:
        return self._node
    def __init__(self, node: ast.Module, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.body: ast.stmt = node.body
        self.type_ignores: ast.type_ignore = node.type_ignores
    def construct(self)->ast.Module:
        return ast.Module(
            self.body,
            self.type_ignores,
        )

class InteractiveBuilderNode(StackSupportNode, typing=ast.Interactive):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Interactive
    """
    @property
    def node(self)->ast.Interactive:
        return self._node
    def __init__(self, node: ast.Interactive, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.body: ast.stmt = node.body
    def construct(self)->ast.Interactive:
        return ast.Interactive(
            self.body,
        )

class ExpressionBuilderNode(StackSupportNode, typing=ast.Expression):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Expression
    """
    @property
    def node(self)->ast.Expression:
        return self._node
    def __init__(self, node: ast.Expression, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.body: ast.expr = node.body
    def construct(self)->ast.Expression:
        return ast.Expression(
            self.body,
        )

class FunctionTypeBuilderNode(StackSupportNode, typing=ast.FunctionType):
    """
    This is a node to support the 
    creation of ast nodes of variety
    FunctionType
    """
    @property
    def node(self)->ast.FunctionType:
        return self._node
    def __init__(self, node: ast.FunctionType, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.argtypes: ast.expr = node.argtypes
        self.returns: ast.expr = node.returns
    def construct(self)->ast.FunctionType:
        return ast.FunctionType(
            self.argtypes,
            self.returns,
        )

class stmtBuilderNode(StackSupportNode, typing=ast.stmt):
    """
    This is a node to support the 
    creation of ast nodes of variety
    stmt
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    FunctionDef
    """
    @property
    def node(self)->ast.FunctionDef:
        return self._node
    def __init__(self, node: ast.FunctionDef, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.name: object = node.name
        self.args: ast.arguments = node.args
        self.body: ast.stmt = node.body
        self.decorator_list: ast.expr = node.decorator_list
        self.returns: ast.expr = node.returns
        self.type_comment: object = node.type_comment
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
    This is a node to support the 
    creation of ast nodes of variety
    AsyncFunctionDef
    """
    @property
    def node(self)->ast.AsyncFunctionDef:
        return self._node
    def __init__(self, node: ast.AsyncFunctionDef, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.name: object = node.name
        self.args: ast.arguments = node.args
        self.body: ast.stmt = node.body
        self.decorator_list: ast.expr = node.decorator_list
        self.returns: ast.expr = node.returns
        self.type_comment: object = node.type_comment
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
    This is a node to support the 
    creation of ast nodes of variety
    ClassDef
    """
    @property
    def node(self)->ast.ClassDef:
        return self._node
    def __init__(self, node: ast.ClassDef, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.name: object = node.name
        self.bases: ast.expr = node.bases
        self.keywords: ast.keyword = node.keywords
        self.body: ast.stmt = node.body
        self.decorator_list: ast.expr = node.decorator_list
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
    This is a node to support the 
    creation of ast nodes of variety
    Return
    """
    @property
    def node(self)->ast.Return:
        return self._node
    def __init__(self, node: ast.Return, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: ast.expr = node.value
    def construct(self)->ast.Return:
        return ast.Return(
            self.value,
        )

class DeleteBuilderNode(StackSupportNode, typing=ast.Delete):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Delete
    """
    @property
    def node(self)->ast.Delete:
        return self._node
    def __init__(self, node: ast.Delete, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.targets: ast.expr = node.targets
    def construct(self)->ast.Delete:
        return ast.Delete(
            self.targets,
        )

class AssignBuilderNode(StackSupportNode, typing=ast.Assign):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Assign
    """
    @property
    def node(self)->ast.Assign:
        return self._node
    def __init__(self, node: ast.Assign, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.targets: ast.expr = node.targets
        self.value: ast.expr = node.value
        self.type_comment: object = node.type_comment
    def construct(self)->ast.Assign:
        return ast.Assign(
            self.targets,
            self.value,
            self.type_comment,
        )

class AugAssignBuilderNode(StackSupportNode, typing=ast.AugAssign):
    """
    This is a node to support the 
    creation of ast nodes of variety
    AugAssign
    """
    @property
    def node(self)->ast.AugAssign:
        return self._node
    def __init__(self, node: ast.AugAssign, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.target: ast.expr = node.target
        self.op: ast.operator = node.op
        self.value: ast.expr = node.value
    def construct(self)->ast.AugAssign:
        return ast.AugAssign(
            self.target,
            self.op,
            self.value,
        )

class AnnAssignBuilderNode(StackSupportNode, typing=ast.AnnAssign):
    """
    This is a node to support the 
    creation of ast nodes of variety
    AnnAssign
    """
    @property
    def node(self)->ast.AnnAssign:
        return self._node
    def __init__(self, node: ast.AnnAssign, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.target: ast.expr = node.target
        self.annotation: ast.expr = node.annotation
        self.value: ast.expr = node.value
        self.simple: object = node.simple
    def construct(self)->ast.AnnAssign:
        return ast.AnnAssign(
            self.target,
            self.annotation,
            self.value,
            self.simple,
        )

class ForBuilderNode(StackSupportNode, typing=ast.For):
    """
    This is a node to support the 
    creation of ast nodes of variety
    For
    """
    @property
    def node(self)->ast.For:
        return self._node
    def __init__(self, node: ast.For, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.target: ast.expr = node.target
        self.iter: ast.expr = node.iter
        self.body: ast.stmt = node.body
        self.orelse: ast.stmt = node.orelse
        self.type_comment: object = node.type_comment
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
    This is a node to support the 
    creation of ast nodes of variety
    AsyncFor
    """
    @property
    def node(self)->ast.AsyncFor:
        return self._node
    def __init__(self, node: ast.AsyncFor, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.target: ast.expr = node.target
        self.iter: ast.expr = node.iter
        self.body: ast.stmt = node.body
        self.orelse: ast.stmt = node.orelse
        self.type_comment: object = node.type_comment
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
    This is a node to support the 
    creation of ast nodes of variety
    While
    """
    @property
    def node(self)->ast.While:
        return self._node
    def __init__(self, node: ast.While, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.test: ast.expr = node.test
        self.body: ast.stmt = node.body
        self.orelse: ast.stmt = node.orelse
    def construct(self)->ast.While:
        return ast.While(
            self.test,
            self.body,
            self.orelse,
        )

class IfBuilderNode(StackSupportNode, typing=ast.If):
    """
    This is a node to support the 
    creation of ast nodes of variety
    If
    """
    @property
    def node(self)->ast.If:
        return self._node
    def __init__(self, node: ast.If, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.test: ast.expr = node.test
        self.body: ast.stmt = node.body
        self.orelse: ast.stmt = node.orelse
    def construct(self)->ast.If:
        return ast.If(
            self.test,
            self.body,
            self.orelse,
        )

class WithBuilderNode(StackSupportNode, typing=ast.With):
    """
    This is a node to support the 
    creation of ast nodes of variety
    With
    """
    @property
    def node(self)->ast.With:
        return self._node
    def __init__(self, node: ast.With, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.items: ast.withitem = node.items
        self.body: ast.stmt = node.body
        self.type_comment: object = node.type_comment
    def construct(self)->ast.With:
        return ast.With(
            self.items,
            self.body,
            self.type_comment,
        )

class AsyncWithBuilderNode(StackSupportNode, typing=ast.AsyncWith):
    """
    This is a node to support the 
    creation of ast nodes of variety
    AsyncWith
    """
    @property
    def node(self)->ast.AsyncWith:
        return self._node
    def __init__(self, node: ast.AsyncWith, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.items: ast.withitem = node.items
        self.body: ast.stmt = node.body
        self.type_comment: object = node.type_comment
    def construct(self)->ast.AsyncWith:
        return ast.AsyncWith(
            self.items,
            self.body,
            self.type_comment,
        )

class RaiseBuilderNode(StackSupportNode, typing=ast.Raise):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Raise
    """
    @property
    def node(self)->ast.Raise:
        return self._node
    def __init__(self, node: ast.Raise, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.exc: ast.expr = node.exc
        self.cause: ast.expr = node.cause
    def construct(self)->ast.Raise:
        return ast.Raise(
            self.exc,
            self.cause,
        )

class TryBuilderNode(StackSupportNode, typing=ast.Try):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Try
    """
    @property
    def node(self)->ast.Try:
        return self._node
    def __init__(self, node: ast.Try, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.body: ast.stmt = node.body
        self.handlers: ast.excepthandler = node.handlers
        self.orelse: ast.stmt = node.orelse
        self.finalbody: ast.stmt = node.finalbody
    def construct(self)->ast.Try:
        return ast.Try(
            self.body,
            self.handlers,
            self.orelse,
            self.finalbody,
        )

class AssertBuilderNode(StackSupportNode, typing=ast.Assert):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Assert
    """
    @property
    def node(self)->ast.Assert:
        return self._node
    def __init__(self, node: ast.Assert, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.test: ast.expr = node.test
        self.msg: ast.expr = node.msg
    def construct(self)->ast.Assert:
        return ast.Assert(
            self.test,
            self.msg,
        )

class ImportBuilderNode(StackSupportNode, typing=ast.Import):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Import
    """
    @property
    def node(self)->ast.Import:
        return self._node
    def __init__(self, node: ast.Import, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.names: ast.alias = node.names
    def construct(self)->ast.Import:
        return ast.Import(
            self.names,
        )

class ImportFromBuilderNode(StackSupportNode, typing=ast.ImportFrom):
    """
    This is a node to support the 
    creation of ast nodes of variety
    ImportFrom
    """
    @property
    def node(self)->ast.ImportFrom:
        return self._node
    def __init__(self, node: ast.ImportFrom, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.module: object = node.module
        self.names: ast.alias = node.names
        self.level: object = node.level
    def construct(self)->ast.ImportFrom:
        return ast.ImportFrom(
            self.module,
            self.names,
            self.level,
        )

class GlobalBuilderNode(StackSupportNode, typing=ast.Global):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Global
    """
    @property
    def node(self)->ast.Global:
        return self._node
    def __init__(self, node: ast.Global, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.names: object = node.names
    def construct(self)->ast.Global:
        return ast.Global(
            self.names,
        )

class NonlocalBuilderNode(StackSupportNode, typing=ast.Nonlocal):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Nonlocal
    """
    @property
    def node(self)->ast.Nonlocal:
        return self._node
    def __init__(self, node: ast.Nonlocal, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.names: object = node.names
    def construct(self)->ast.Nonlocal:
        return ast.Nonlocal(
            self.names,
        )

class ExprBuilderNode(StackSupportNode, typing=ast.Expr):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Expr
    """
    @property
    def node(self)->ast.Expr:
        return self._node
    def __init__(self, node: ast.Expr, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: ast.expr = node.value
    def construct(self)->ast.Expr:
        return ast.Expr(
            self.value,
        )

class PassBuilderNode(StackSupportNode, typing=ast.Pass):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Pass
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    Break
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    Continue
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    expr
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    BoolOp
    """
    @property
    def node(self)->ast.BoolOp:
        return self._node
    def __init__(self, node: ast.BoolOp, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.op: ast.boolop = node.op
        self.values: ast.expr = node.values
    def construct(self)->ast.BoolOp:
        return ast.BoolOp(
            self.op,
            self.values,
        )

class NamedExprBuilderNode(StackSupportNode, typing=ast.NamedExpr):
    """
    This is a node to support the 
    creation of ast nodes of variety
    NamedExpr
    """
    @property
    def node(self)->ast.NamedExpr:
        return self._node
    def __init__(self, node: ast.NamedExpr, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.target: ast.expr = node.target
        self.value: ast.expr = node.value
    def construct(self)->ast.NamedExpr:
        return ast.NamedExpr(
            self.target,
            self.value,
        )

class BinOpBuilderNode(StackSupportNode, typing=ast.BinOp):
    """
    This is a node to support the 
    creation of ast nodes of variety
    BinOp
    """
    @property
    def node(self)->ast.BinOp:
        return self._node
    def __init__(self, node: ast.BinOp, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.left: ast.expr = node.left
        self.op: ast.operator = node.op
        self.right: ast.expr = node.right
    def construct(self)->ast.BinOp:
        return ast.BinOp(
            self.left,
            self.op,
            self.right,
        )

class UnaryOpBuilderNode(StackSupportNode, typing=ast.UnaryOp):
    """
    This is a node to support the 
    creation of ast nodes of variety
    UnaryOp
    """
    @property
    def node(self)->ast.UnaryOp:
        return self._node
    def __init__(self, node: ast.UnaryOp, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.op: ast.unaryop = node.op
        self.operand: ast.expr = node.operand
    def construct(self)->ast.UnaryOp:
        return ast.UnaryOp(
            self.op,
            self.operand,
        )

class LambdaBuilderNode(StackSupportNode, typing=ast.Lambda):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Lambda
    """
    @property
    def node(self)->ast.Lambda:
        return self._node
    def __init__(self, node: ast.Lambda, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.args: ast.arguments = node.args
        self.body: ast.expr = node.body
    def construct(self)->ast.Lambda:
        return ast.Lambda(
            self.args,
            self.body,
        )

class IfExpBuilderNode(StackSupportNode, typing=ast.IfExp):
    """
    This is a node to support the 
    creation of ast nodes of variety
    IfExp
    """
    @property
    def node(self)->ast.IfExp:
        return self._node
    def __init__(self, node: ast.IfExp, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.test: ast.expr = node.test
        self.body: ast.expr = node.body
        self.orelse: ast.expr = node.orelse
    def construct(self)->ast.IfExp:
        return ast.IfExp(
            self.test,
            self.body,
            self.orelse,
        )

class DictBuilderNode(StackSupportNode, typing=ast.Dict):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Dict
    """
    @property
    def node(self)->ast.Dict:
        return self._node
    def __init__(self, node: ast.Dict, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.keys: ast.expr = node.keys
        self.values: ast.expr = node.values
    def construct(self)->ast.Dict:
        return ast.Dict(
            self.keys,
            self.values,
        )

class SetBuilderNode(StackSupportNode, typing=ast.Set):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Set
    """
    @property
    def node(self)->ast.Set:
        return self._node
    def __init__(self, node: ast.Set, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.elts: ast.expr = node.elts
    def construct(self)->ast.Set:
        return ast.Set(
            self.elts,
        )

class ListCompBuilderNode(StackSupportNode, typing=ast.ListComp):
    """
    This is a node to support the 
    creation of ast nodes of variety
    ListComp
    """
    @property
    def node(self)->ast.ListComp:
        return self._node
    def __init__(self, node: ast.ListComp, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.elt: ast.expr = node.elt
        self.generators: ast.comprehension = node.generators
    def construct(self)->ast.ListComp:
        return ast.ListComp(
            self.elt,
            self.generators,
        )

class SetCompBuilderNode(StackSupportNode, typing=ast.SetComp):
    """
    This is a node to support the 
    creation of ast nodes of variety
    SetComp
    """
    @property
    def node(self)->ast.SetComp:
        return self._node
    def __init__(self, node: ast.SetComp, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.elt: ast.expr = node.elt
        self.generators: ast.comprehension = node.generators
    def construct(self)->ast.SetComp:
        return ast.SetComp(
            self.elt,
            self.generators,
        )

class DictCompBuilderNode(StackSupportNode, typing=ast.DictComp):
    """
    This is a node to support the 
    creation of ast nodes of variety
    DictComp
    """
    @property
    def node(self)->ast.DictComp:
        return self._node
    def __init__(self, node: ast.DictComp, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.key: ast.expr = node.key
        self.value: ast.expr = node.value
        self.generators: ast.comprehension = node.generators
    def construct(self)->ast.DictComp:
        return ast.DictComp(
            self.key,
            self.value,
            self.generators,
        )

class GeneratorExpBuilderNode(StackSupportNode, typing=ast.GeneratorExp):
    """
    This is a node to support the 
    creation of ast nodes of variety
    GeneratorExp
    """
    @property
    def node(self)->ast.GeneratorExp:
        return self._node
    def __init__(self, node: ast.GeneratorExp, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.elt: ast.expr = node.elt
        self.generators: ast.comprehension = node.generators
    def construct(self)->ast.GeneratorExp:
        return ast.GeneratorExp(
            self.elt,
            self.generators,
        )

class AwaitBuilderNode(StackSupportNode, typing=ast.Await):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Await
    """
    @property
    def node(self)->ast.Await:
        return self._node
    def __init__(self, node: ast.Await, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: ast.expr = node.value
    def construct(self)->ast.Await:
        return ast.Await(
            self.value,
        )

class YieldBuilderNode(StackSupportNode, typing=ast.Yield):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Yield
    """
    @property
    def node(self)->ast.Yield:
        return self._node
    def __init__(self, node: ast.Yield, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: ast.expr = node.value
    def construct(self)->ast.Yield:
        return ast.Yield(
            self.value,
        )

class YieldFromBuilderNode(StackSupportNode, typing=ast.YieldFrom):
    """
    This is a node to support the 
    creation of ast nodes of variety
    YieldFrom
    """
    @property
    def node(self)->ast.YieldFrom:
        return self._node
    def __init__(self, node: ast.YieldFrom, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: ast.expr = node.value
    def construct(self)->ast.YieldFrom:
        return ast.YieldFrom(
            self.value,
        )

class CompareBuilderNode(StackSupportNode, typing=ast.Compare):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Compare
    """
    @property
    def node(self)->ast.Compare:
        return self._node
    def __init__(self, node: ast.Compare, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.left: ast.expr = node.left
        self.ops: ast.cmpop = node.ops
        self.comparators: ast.expr = node.comparators
    def construct(self)->ast.Compare:
        return ast.Compare(
            self.left,
            self.ops,
            self.comparators,
        )

class CallBuilderNode(StackSupportNode, typing=ast.Call):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Call
    """
    @property
    def node(self)->ast.Call:
        return self._node
    def __init__(self, node: ast.Call, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.func: ast.expr = node.func
        self.args: ast.expr = node.args
        self.keywords: ast.keyword = node.keywords
    def construct(self)->ast.Call:
        return ast.Call(
            self.func,
            self.args,
            self.keywords,
        )

class FormattedValueBuilderNode(StackSupportNode, typing=ast.FormattedValue):
    """
    This is a node to support the 
    creation of ast nodes of variety
    FormattedValue
    """
    @property
    def node(self)->ast.FormattedValue:
        return self._node
    def __init__(self, node: ast.FormattedValue, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: ast.expr = node.value
        self.conversion: object = node.conversion
        self.format_spec: ast.expr = node.format_spec
    def construct(self)->ast.FormattedValue:
        return ast.FormattedValue(
            self.value,
            self.conversion,
            self.format_spec,
        )

class JoinedStrBuilderNode(StackSupportNode, typing=ast.JoinedStr):
    """
    This is a node to support the 
    creation of ast nodes of variety
    JoinedStr
    """
    @property
    def node(self)->ast.JoinedStr:
        return self._node
    def __init__(self, node: ast.JoinedStr, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.values: ast.expr = node.values
    def construct(self)->ast.JoinedStr:
        return ast.JoinedStr(
            self.values,
        )

class ConstantBuilderNode(StackSupportNode, typing=ast.Constant):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Constant
    """
    @property
    def node(self)->ast.Constant:
        return self._node
    def __init__(self, node: ast.Constant, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: object = node.value
        self.kind: object = node.kind
    def construct(self)->ast.Constant:
        return ast.Constant(
            self.value,
            self.kind,
        )

class AttributeBuilderNode(StackSupportNode, typing=ast.Attribute):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Attribute
    """
    @property
    def node(self)->ast.Attribute:
        return self._node
    def __init__(self, node: ast.Attribute, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: ast.expr = node.value
        self.attr: object = node.attr
        self.ctx: ast.expr_context = node.ctx
    def construct(self)->ast.Attribute:
        return ast.Attribute(
            self.value,
            self.attr,
            self.ctx,
        )

class SubscriptBuilderNode(StackSupportNode, typing=ast.Subscript):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Subscript
    """
    @property
    def node(self)->ast.Subscript:
        return self._node
    def __init__(self, node: ast.Subscript, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: ast.expr = node.value
        self.slice: ast.expr = node.slice
        self.ctx: ast.expr_context = node.ctx
    def construct(self)->ast.Subscript:
        return ast.Subscript(
            self.value,
            self.slice,
            self.ctx,
        )

class StarredBuilderNode(StackSupportNode, typing=ast.Starred):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Starred
    """
    @property
    def node(self)->ast.Starred:
        return self._node
    def __init__(self, node: ast.Starred, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.value: ast.expr = node.value
        self.ctx: ast.expr_context = node.ctx
    def construct(self)->ast.Starred:
        return ast.Starred(
            self.value,
            self.ctx,
        )

class NameBuilderNode(StackSupportNode, typing=ast.Name):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Name
    """
    @property
    def node(self)->ast.Name:
        return self._node
    def __init__(self, node: ast.Name, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.id: object = node.id
        self.ctx: ast.expr_context = node.ctx
    def construct(self)->ast.Name:
        return ast.Name(
            self.id,
            self.ctx,
        )

class ListBuilderNode(StackSupportNode, typing=ast.List):
    """
    This is a node to support the 
    creation of ast nodes of variety
    List
    """
    @property
    def node(self)->ast.List:
        return self._node
    def __init__(self, node: ast.List, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.elts: ast.expr = node.elts
        self.ctx: ast.expr_context = node.ctx
    def construct(self)->ast.List:
        return ast.List(
            self.elts,
            self.ctx,
        )

class TupleBuilderNode(StackSupportNode, typing=ast.Tuple):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Tuple
    """
    @property
    def node(self)->ast.Tuple:
        return self._node
    def __init__(self, node: ast.Tuple, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.elts: ast.expr = node.elts
        self.ctx: ast.expr_context = node.ctx
    def construct(self)->ast.Tuple:
        return ast.Tuple(
            self.elts,
            self.ctx,
        )

class expr_contextBuilderNode(StackSupportNode, typing=ast.expr_context):
    """
    This is a node to support the 
    creation of ast nodes of variety
    expr_context
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    Load
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    Store
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    Del
    """
    @property
    def node(self)->ast.Del:
        return self._node
    def __init__(self, node: ast.Del, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.Del:
        return ast.Del(
            
        )

class SliceBuilderNode(StackSupportNode, typing=ast.Slice):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Slice
    """
    @property
    def node(self)->ast.Slice:
        return self._node
    def __init__(self, node: ast.Slice, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.lower: ast.expr = node.lower
        self.upper: ast.expr = node.upper
        self.step: ast.expr = node.step
    def construct(self)->ast.Slice:
        return ast.Slice(
            self.lower,
            self.upper,
            self.step,
        )

class boolopBuilderNode(StackSupportNode, typing=ast.boolop):
    """
    This is a node to support the 
    creation of ast nodes of variety
    boolop
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    And
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    Or
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    operator
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    Add
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    Sub
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    Mult
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    MatMult
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    Div
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    Mod
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    Pow
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    LShift
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    RShift
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    BitOr
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    BitXor
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    BitAnd
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    FloorDiv
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    unaryop
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    Invert
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    Not
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    UAdd
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    USub
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    cmpop
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    Eq
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    NotEq
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    Lt
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    LtE
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    Gt
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    GtE
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    Is
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    IsNot
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    In
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    NotIn
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    comprehension
    """
    @property
    def node(self)->ast.comprehension:
        return self._node
    def __init__(self, node: ast.comprehension, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.comprehension:
        return ast.comprehension(
            
        )

class excepthandlerBuilderNode(StackSupportNode, typing=ast.excepthandler):
    """
    This is a node to support the 
    creation of ast nodes of variety
    excepthandler
    """
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
    This is a node to support the 
    creation of ast nodes of variety
    ExceptHandler
    """
    @property
    def node(self)->ast.ExceptHandler:
        return self._node
    def __init__(self, node: ast.ExceptHandler, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.type: ast.expr = node.type
        self.name: object = node.name
        self.body: ast.stmt = node.body
    def construct(self)->ast.ExceptHandler:
        return ast.ExceptHandler(
            self.type,
            self.name,
            self.body,
        )

class argumentsBuilderNode(StackSupportNode, typing=ast.arguments):
    """
    This is a node to support the 
    creation of ast nodes of variety
    arguments
    """
    @property
    def node(self)->ast.arguments:
        return self._node
    def __init__(self, node: ast.arguments, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.arguments:
        return ast.arguments(
            
        )

class argBuilderNode(StackSupportNode, typing=ast.arg):
    """
    This is a node to support the 
    creation of ast nodes of variety
    arg
    """
    @property
    def node(self)->ast.arg:
        return self._node
    def __init__(self, node: ast.arg, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.arg:
        return ast.arg(
            
        )

class keywordBuilderNode(StackSupportNode, typing=ast.keyword):
    """
    This is a node to support the 
    creation of ast nodes of variety
    keyword
    """
    @property
    def node(self)->ast.keyword:
        return self._node
    def __init__(self, node: ast.keyword, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.keyword:
        return ast.keyword(
            
        )

class aliasBuilderNode(StackSupportNode, typing=ast.alias):
    """
    This is a node to support the 
    creation of ast nodes of variety
    alias
    """
    @property
    def node(self)->ast.alias:
        return self._node
    def __init__(self, node: ast.alias, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.alias:
        return ast.alias(
            
        )

class withitemBuilderNode(StackSupportNode, typing=ast.withitem):
    """
    This is a node to support the 
    creation of ast nodes of variety
    withitem
    """
    @property
    def node(self)->ast.withitem:
        return self._node
    def __init__(self, node: ast.withitem, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.withitem:
        return ast.withitem(
            
        )

class type_ignoreBuilderNode(StackSupportNode, typing=ast.type_ignore):
    """
    This is a node to support the 
    creation of ast nodes of variety
    type_ignore
    """
    @property
    def node(self)->ast.type_ignore:
        return self._node
    def __init__(self, node: ast.type_ignore, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        
    def construct(self)->ast.type_ignore:
        return ast.type_ignore(
            
        )

class TypeIgnoreBuilderNode(StackSupportNode, typing=ast.TypeIgnore):
    """
    This is a node to support the 
    creation of ast nodes of variety
    TypeIgnore
    """
    @property
    def node(self)->ast.TypeIgnore:
        return self._node
    def __init__(self, node: ast.TypeIgnore, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.lineno: object = node.lineno
        self.tag: object = node.tag
    def construct(self)->ast.TypeIgnore:
        return ast.TypeIgnore(
            self.lineno,
            self.tag,
        )

class StrBuilderNode(StackSupportNode, typing=ast.Str):
    """
    This is a node to support the 
    creation of ast nodes of variety
    Str
    """
    @property
    def node(self)->ast.Str:
        return self._node
    def __init__(self, node: ast.Str, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        self.values: ast.expr = node.values
    def construct(self)->ast.Str:
        return ast.Str(
            self.values,
        )
