from typing import Any, Union, Type, List, Dict, Optional, Generator

import astroid
from dataclasses import dataclass

Literal = Union[int, str, float, complex, ]
LiteralOrNode = Union[Literal, astroid.NodeNG]





@dataclass
class info_packet():
    """
    Contains information about a given child in a compact
    and easily usable format.
    """
    is_list: bool
    parent: "astroid_support_node"
    value: LiteralOrNode
    field: str
    index: Optional[int] = None

    def derivative(self, value: Optional[Literal])->"info_packet":
        """
        Produce a new infopacket with the same
        parent information and field information.

        Usable for replacement purposes. Contains
        information given in "value"

        :param value: The information to set
        :return: A new info_packet
        """


class astroid_support_node():
    """
    Represents an under construction
    astroid tree, with associated
    utility methods.
    """
    #Displays original node
    #Displays node under construction.
    #Contains utility methods such as iterators and
    #push methods
    def push(self, node: action_packet):

class astroid_support_node():
    """
    A support node for building astroid
    features. Contains many utility functions.
    Designed to be entirely pure, with
    no side effects.
    """
    node: astroid.NodeNG
    fields: Dict[str, List[LiteralOrNode], Optional[LiteralOrNode]]
    parent: Optional["astroid_support_node"] = None
    def push(self, node: astroid.NodeNG)->"astroid_support_node":
        """Creates a new astroid support node to support the given astroid node"""
        pass
    def pop(self)->"astroid_support_node":
        """Builds the current self as a node. """
        pass
    def open(self, node: astroid.NodeNG):
        """
         Opens a new context at the given node.
         Locks the existing context to prevent editing conflicts.
         Promises to infer on the context created in
         """
    def iterate_children(self)->Generator[info_packet]:
        """Iterates over all children, returning child packets for each feature"""
        pass