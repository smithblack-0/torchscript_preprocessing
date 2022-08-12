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



class NodeBuilder():
    """
    A node builder is a collection consisting
    of an original node, and features to place
    in a new one. It is available to deeper
    elements in a stack, and generally indicates
    where useful features may be found"

    They exist to help make building easy by, for instance,
    automatically reshuffling call orders.
    """
    standard_registry: Dict[Type[ast.AST], Type["NodeBuilder"]] = {}
    generics_registry: Dict[Callable[[Type[ast.AST]], bool], Type["NodeBuilder"]] = {}
    default_registry: Type["NodeBuilder"] = None
    def __init_subclass__(cls, typing: Union[Type[ast.AST], Callable[[Type[ast.AST]], bool], str] = None):
        """
        When a subclass is created from this class,
        it is automatically registered to one of three
        locations - the standard registry, the generics registry,
        or the defaults registry.

        Which it is registered to will depend on the nature of the passed
        typing parameter. For example:
        ```
        class ClassBuilder(NodeBuilder, typing=ast.ClassDef):
            ... stuff
        ```
        A ast pass results in a standard registration
        A callable represents some sort of generic or condition.
        A pass of "default" results in a default registration
        """

        if typing is None:
            raise ValueError("Must pass typing keyword on class creation")
        if callable(typing):
            cls.generics_registry[typing] = cls
        elif isinstance(typing, str) and typing == "default":
            cls.default_registry = cls
        elif issubclass(typing, ast.AST):
            cls.standard_registry[typing] = cls
        else:
            raise ValueError("Typing of name %s is illegal" % typing)
    def __new__(cls, node: ast.AST, *args, **kwargs):
        """Check the standard, then generic, and finally default registry."""
        std  = [isinstance(node, key) for key in cls.standard_registry.keys()]
        for key in cls.standard_registry.keys():
            if isinstance(node, key):
                return cls.standard_registry[key](node)
        for is_case in cls.generics_registry:
            if is_case(node):
                return cls.generics_registry[is_case](node)
        if cls.default_registry is not None:
            return cls.default_registry(node)
        raise KeyError("Ndoe Type not found")
    def __init__(self, node: ast.AST):
        self.__start_state = None
        self.__features = None
        self._original = node
    @property
    def original(self):
        """Needs to be implimented with typing"""
        return self._original
    def start_record(self):
        """Starts recording features to transfer to a new node"""
        self.__start_state = self.__dict__
    def end_record(self):
        """Ends recording of features to transfer to node"""
        self.__features = [key for key, value in self.__dict__.items()
                           if key not in self.__start_state]
    def finish(self)->ast.AST:
        """Build the node"""
        node = copy.deepcopy(self.original)
        for key in self.__features:
            value = getattr(self, key)
            setattr(node, key, value)
        return node

class ClassBuilder(NodeBuilder, typing=ast.ClassDef):
    """
    A class builder. Helps to build a class

    Anything not explicitly placed in the builder
    will not be found in the resulting class node
    """
    typing = ast.ClassDef
    @property
    def original(self)->ast.ClassDef:
        return self._original
    def __init__(self, original: ast.ClassDef):
        super().__init__(original)

        self.start_record()
        self.body: List[ast.AST] = []
        self.bases: List[ast.AST] = []
        self.keywords: List[ast.AST] = []
        self.end_record()
    def finish(self)->ast.ClassDef:
        return super().finish()

class argumentsBuilder(NodeBuilder, typing=ast.arguments):
    """
    A arguments builder. Builds a new
    argument. Also a place to keep
    useful ast info.
    """
    @property
    def original(self)->ast.arguments:
        return self._original
    def __init__(self, arguments: ast.arguments):
        super().__init__(arguments)

        self.original = arguments

        #Define node features
        self.start_record()
        self.args: List[ast.AST] = []
        self.defaults: List[ast.AST] = []
        self.kwarg: Optional[ast.AST] = None
        self.kw_defaults: List[ast.AST] = []
        self.kwonlyargs: List[ast.AST] = []
        self.posonlyargs: List[ast.AST] = []
        self.vararg: List[ast.AST] = []
        self.end_record()
    def finish(self)->ast.arguments:
        return super().finish()

class FunctionBuilder(NodeBuilder, typing=ast.FunctionDef):
    """
    A function builder. Builds a new function
    out of an original function.
    """
    @property
    def original(self)->ast.FunctionDef:
        return self._original
    def __init__(self, functionDef: ast.FunctionDef):
        super().__init__()
        self.original = functionDef

        #Define node features
        self.start_record()
        self.body: List[ast.AST] = []
        self.args: Optional[ast.arguments] = None
        self.decorator_list: List[ast.AST] = []
        self.returns: Optional[ast.AST] = None
        self.end_record()
    def finish(self) ->ast.FunctionDef:
        return super().finish()

class ModuleBuilder(NodeBuilder, typing=ast.Module):
    """
    A builder for constructing mdoules
    """
    @property
    def original(self)->ast.Module:
        return self._original
    def __init__(self, module: ast.Module):
        super().__init__(module)
        #Node attributes
        self.start_record()
        self.body: List[ast.AST] = []
        self.end_record()
    def finish(self) ->ast.Module:
        return super().finish()

def _is_body_generic(node: ast.AST):
    if hasattr(node, "body"):
        return True
    return False
BodyTypes = \
    Union[ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
    ast.For, ast.AsyncFor, ast.While, ast.If, ast.With, ast.AsyncWith,
    ast.Try, ast.Lambda, ast.IfExp]

class GenericBodyBuilder(NodeBuilder, typing=_is_body_generic):
    """
    Activated when nothing else will, and we have
    a body statement
    """
    @property
    def original(self)->BodyTypes:
        return self._original
    def __init__(self, node: BodyTypes):
        super().__init__(node)
        self.start_record()
        self.body: List[ast.AST] = []
        self.end_record()
    def finish(self) ->BodyTypes:
        return super().finish()


class Generic(NodeBuilder, typing="default"):
    def __init__(self, node: ast.AST):
        super().__init__(node)
        self.start_record()
        self.end_record()


