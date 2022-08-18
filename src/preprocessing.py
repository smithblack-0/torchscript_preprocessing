"""
The preprocessing algorithm will attempt to resolve

"""
import copy
from dataclasses import dataclass

import astroid
import astunparse
import builder
import inspect
import StringExec



from typing import List, Dict, Optional, Type, Tuple, Callable, Generator, Any
from enum import Enum
from src import construction_database

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




def place_edit_packet_on_node(node: astroid.NodeNG, packet: "edit_packet"):
    """Places an edit packet onto the node. Unusual side effect, so isolated in its own function"""
    node._packet = packet

def get_edit_packet_from_node(node: astroid.NodeNG)->"edit_packet":
    """Gets from a node the associated edit packet"""
    assert hasattr(node, "_packet")
    return node._packet


class AbstractFieldEditor():
    """
    Allows for modification of
    a particular field
    """
    field_type: Any
    field_value: Any
    def __init__(self,
                 parent_node: astroid.NodeNG,
                 fieldname: str):
        self.parent = parent_node
        self.fieldname = fieldname

class DirectFieldEditor(AbstractFieldEditor):
    """Edits fields which are placed directly on a node"""
    @property
    def field_value(self):
        return getattr(self.parent, self.fieldname)
    def __init__(self, parent, fieldname):
        super().__init__(parent, fieldname)

class ListFieldEditor(AbstractFieldEditor):
    """
    Edits things found in a list. Supports insertion before,
    after, replacement, and deletion
    """
    @property
    def _lst(self):
        return getattr(self.parent, self.fieldname)

    @property
    def field_index(self):
        return self._lst.index(self.field_value)
    @property
    def field_value(self):
        return self._field_value
    @field_value.setter
    def field_value(self, value: Any):
        lst = self._lst
        lst[self.field_index] = value
        self._field_value = value

    def insert_before(self, value: Any):


    def __init__(self, parent, fieldname, field_value):
        super().__init__(parent, fieldname)
        self._field_value = field_value

class FieldEditor():
    """
    This class allows for the editing of fields.

    It contains field information, and methods
    which can be utilized to set the field in
    a new
    """

class Field():
    """
    A representation of a field

    Things can be put here
    """

class FieldList():
    """
    A representation of a
    """
class UnboundFieldListNode():
    """
    A node representing an entry in a
    list. It has not yet been bound
    to a position.
    """
    def __init__(self,
                 parent_node: astroid.NodeNG,
                 fieldname: str,
                 fieldtype: Type[Any],
                 fieldvalue: Any,
                 ):
        self.parent = parent_node
        self.fieldname = fieldname
        self.fieldtype = fieldtype
        self.fieldvalue = fieldvalue
    def derivative(self, value: Any):
        pass

class FieldListNode():
    """
    A node representing an entry
    in a list. It has as of this point
    been bound to a position.
    """
    @property
    def pos(self):
        pass
    def __init__(self,
                 parent_node: astroid.NodeNG,
                 fieldname: str,
                 fieldtype: Type[Any],
                 fieldvalue: Any,
                 ):
        self.parent = parent_node
        self.fieldname = fieldname
        self.fieldtype = fieldtype
        self.fieldvalue = fieldvalue
    def derivative(self):


class Field():


class Field():
    """
    This class has two important responsibility

    Explore the fields attached to a particular node.
    """
    def __init__(self,
                 parent_node: astroid.NodeNG,
                 fieldname: str,
                 fieldtype: Type[Any],
                 fieldvalue: Any,
                 ):
        self.parent = parent_node
        self.fieldname = fieldname
        self.fieldtype = fieldtype
        self.fieldvalue = fieldvalue
    def derivative(self):
        """
        Creates a copy of this with a new field value, which
        will land in the same place.
        """
    def commit(self):
        """
        Commit this feature into the indicated field.
        For lists, this will commit it to the end of the list

        :return:
        """
    def append(self):
        """
        Append everything to list
        :return:
        """


class Editor():
    """
    This class has a single important responsibility

    Explore the nodes which are out there. Return
    the needed information as an info packet
    """
    def iterate_children(self) -> Generator[field_packet, None, None]:
        """
        Iterates over the children of an astroid node.
        Yields information for each child as a childinfo packet.
        """
        original = self.original_node
        for child in self.node.get_children():
            field_name = self.node.locate_child(child)
            attr = getattr(self.node, field_name)
            if isinstance(attr, list):
                pos = attr.index(child)
            else:
                pos = None


            yield field_packet(self.node,
                              field_name,
                              type(attr),
                              child,
                              pos)
    def edit(self, item: field_packet):
        """
        Opens a new explorer to examine the details indicated
        on the given field position.
        """
        assert issubclass(field_packet.field_type, astroid.NodeNG)
        return Editor(self.new_node, field_packet)
    def new(self):


    def __init__(self, node: Optional[astroid.NodeNG]= None, _packet: Optional[field_packet] = None):

        if node is not None:
            self.original_node = node
        else:
            self.original_node = _packet.field_value
        self.new_node = self.original_node.__class__()



def make_node_in_context(obj: object)->astroid.NodeNG:
    """
    Makes a node in the context of the broader
    module.
    :return: A astroid node, as part of the broader
    context
    """

def astroid_transform(packet)->Generator[astroid.NodeNG, None, None]:
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
    explorer = Explorer(start_node)
    emitter = NodeEmitter(start_node)
    while True:

    construction = start_node.__class__()
    construction.parent = start_node.parent


    stack: List[Tuple[astroid.NodeNG,]]


def preprocess(node: astroid.NodeNG):
    node = make_node_in_context(node)
    builder = construction_database.BuildNode()
    stack = []
    generator = iterate_children(node)
    while True:
        try:
            packet: info_packet = next(generator)
            subnode = packet.node
            if isinstance(subnode, astroid.NodeNG):
                stack.append((node, generator))

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



