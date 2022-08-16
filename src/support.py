from typing import Any, Union, Type, List, Dict, Optional, Generator

import astroid
from dataclasses import dataclass

Literal = Union[int, str, float, complex, ]
LiteralOrNode = Union[Literal, astroid.NodeNG]

@dataclass
class child_packet():
    """
    Contains information about a given child in a compact
    and easily usable format. Also contains a utility
    method capable of helping to build a new node
    """
    is_list: bool
    parent: "astroid_support_node"
    value: LiteralOrNode
    field: str
    index: Optional[int] = None
    def commit(self, value: Optional[Literal]=None):
        """Commit the given value on the appriate parent field

         May be done multiple times. This appends to a list,
         or sets to a field.

         If value is none, then it copies the original
         value over without change.
         """
        if value is None:
            value = self.value
        if self.index is not None:
            self.parent.fields[self.field].append(value)
        else:
            self.parent.fields[self.field] = value

class astroid_support_node():
    """
    A support node for building astroid
    features.
    """
    node: astroid.NodeNG
    fields: Dict[str, List[LiteralOrNode], Optional[LiteralOrNode]]
    parent: Optional["astroid_support_node"] = None
    def push(self, node: astroid.NodeNG)->"astroid_support_node":
        """Creates a new astroid support node to support the given astroid node"""
        pass
    def pop(self)->astroid.NodeNG:
        """Creates a new independent astroid node, based on children content"""
        pass
    def open(self, node: astroid.NodeNG):
        """
         Opens a new context at the given node.
         Locks the existing context to prevent editing conflicts.
         Promises to infer on the context created in
         """
    def iterate_children(self)->Generator[child_packet]:
        """Iterates over all children, returning child packets for each feature"""
        pass