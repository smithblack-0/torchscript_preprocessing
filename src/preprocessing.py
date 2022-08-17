"""
The preprocessing algorithm will attempt to resolve

"""

import ast
from dataclasses import dataclass

import astroid
import astunparse
import builder
import inspect
import StringExec


from typing import List, Dict, Optional, Type, Tuple, Callable, Generator, Any
from enum import Enum

class FieldTypes(Enum):
    """The kinds of fields you might see"""
    List = list
    Int = int
    Str = str
    Float = float
    Complex = complex
    EllipsisLit = type(Ellipsis)
    TrueBool = True
    FalseBool = False
    NoneLit = None
    Literal = "Literal"

@dataclass
class info_packet():
    """
    A packet of information about an astroid
    child and it's originating node plus
    field
    """
    fieldname: str
    parent: astroid.NodeNG
    child: Any
    is_list: bool


class NodeEmitter():
    """
    Used to build output nodes.
    """

    def emplace(self, packet: info_packet):
        """
        Place the value onto the node of fieldname
        Sets fieldname if not list
        Appends if fieldname is list.
        """
        fieldname = packet.fieldname
        value = packet.child

        if not hasattr(self, fieldname) or not isinstance(getattr(self, fieldname), FieldTypes.List):
            #This is a literal
            setattr(self, fieldname, value)
        else:
            #This is a list
            getattr(self)

        if isinstance(getattr(self, fieldname), FieldTypes.List):
            setattr(self, fieldname, value)



def make_node_in_context(obj: object)->astroid.NodeNG:
    """
    Makes a node in the context of the broader
    module.
    :return: A astroid node, as part of the broader
    context
    """

def astroid_transform(node: astroid.NodeNG)->Generator[astroid.NodeNG, None, None]:
    """
    Transforms something which is an astroid node.
    Yields a generator of astroid nodes as a result
    """

def literal_transform(parent: astroid.NodeNG, value: Any)->Any:
    """
    Transforms something which is not an astroid node.
    Yields a generator of literals as a result
    """



def iterate_children(node: astroid.NodeNG)->Generator[childinfo_packet, None, None]:
    """
    Iterates over the children of an astroid node.
    Yields information for each child as a childinfo packet.
    """
    for child in node.get_children():
        field = node.locate_child(child)
        attr = getattr(node, field)
        if isinstance(attr, list):
            is_list = True
        else:
            is_list = False
        yield childinfo_packet(field, node, child, is_list)



def emplace(node: astroid.NodeNG, fieldname: str, value: childinfo_packet):
    """
    Place the value onto the fieldname
    Sets fieldname if not list
    Appends if fieldname is list.
    """
    if isinstance(getattr(node, fieldname), FieldTypes.List):
        getattr(node, fieldname).append(value)



def preprocess(obj: object):
    start_node = make_node_in_context(obj)
    construction = start_node.__class__()
    construction.parent = start_node.parent


    stack: List[Tuple[astroid.NodeNG,]]


def preprocess(node: astroid.NodeNG):
    node = make_node_in_context(node)
    construction = node.__class__()
    stack = []
    generator = iterate_children(node)
    while True:
        try:
            packet: childinfo_packet = next(generator)
            subnode = packet.child
            if isinstance(subnode, astroid.NodeNG):
                stack.append((node, construction, generator))
                construction = subnode.__class__()
                generator = subnode.get_children()
            else:
                construction = emplace(construction, packet)


        except StopIteration:
             child = node
             node, generator = stack.pop()
             field = node.locate_child(node)
             result_generator = astroid_transform(child)
             for result in result_generator:
                if isinstance(getattr(node, field), list):
                    getattr(node, field).append(result)
                else:
                    setattr(node, field, result)



