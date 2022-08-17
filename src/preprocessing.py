"""
The preprocessing algorithm will attempt to resolve

"""

import ast
import copy
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
    Node = astroid.NodeNG
    TrueBool = True
    FalseBool = False
    NoneLit = None

@dataclass
class info_packet():
    """
    Two responsiblities.

    Store any relevant information about

    A packet of information about an astroid
    child and it's originating node plus
    field
    """
    fieldname: str
    parent: astroid.NodeNG
    node: Any
    is_list: bool
    def derivative(self, value: Any):
        """Creates a copy of the packet, with node changed to value"""
        return info_packet(self.fieldname,
                           self.parent,
                           value,
                           self.is_list)
class NodeExplorer():
    """
    This class has a single important responsibility

    Explore the nodes which are out there. Return
    the needed information as an info packet
    """
    def iterate_children(self) -> Generator[info_packet, None, None]:
        """
        Iterates over the children of an astroid node.
        Yields information for each child as a childinfo packet.
        """
        node = self.node
        for child in node.get_children():
            field = node.locate_child(child)
            attr = getattr(node, field)
            if isinstance(attr, FieldTypes.List):
                is_list = True
            else:
                is_list = False
            yield info_packet(field, node, child, is_list)
    def define_self(self)->info_packet:
        """Defines oneself as an info packet"""
        if self.parent is not None
    def __init__(self, node: astroid.NodeNG):
        self.node = node



class NodeEmitter():
    """
    This class has two responsibilities

    Store finished nodes, and build
    the results when so called.
    """
    def emit_astroid(self)->astroid.NodeNG:
        """Emit the associated astroid node"""
        return self.construction
    def emplace(self, packet: info_packet):
        """
        Place the value onto the node of fieldname
        Sets fieldname if not list
        Appends if fieldname is list.
        """
        assert self.spec.parent is packet.parent
        fieldname = packet.fieldname
        value = packet.node
        if isinstance(value, astroid.NodeNG):
            #Change the parent if it is a node.
            value = copy.deepcopy(value)
            value.parent = self.construction
        if packet.is_list:
            ls = getattr(self.construction, fieldname)
            ls.append(value)
        else:
            setattr(self.construction, fieldname, value)
    def __init__(self, spec: info_packet):
        assert isinstance(spec.node, astroid.NodeNG)
        self.spec = spec
        self.construction = spec.node.__class__()





def make_node_in_context(obj: object)->astroid.NodeNG:
    """
    Makes a node in the context of the broader
    module.
    :return: A astroid node, as part of the broader
    context
    """

def astroid_transform(packet: info_packet)->Generator[astroid.NodeNG, None, None]:
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




def preprocess(obj: object):
    start_node = make_node_in_context(obj)
    explorer = NodeExplorer(start_node)
    emitter = NodeEmitter(start_node)
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
            subnode = packet.node
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



