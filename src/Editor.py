"""
Contains utilities for sanely editing an astroid node.


"""
import copy

import astroid
from typing import List, Any, Dict, Tuple, Type, Union, Optional, Generator

from src.construction_database import DoubleLinkedList


class AbstractEditor():
    """
    Abstract class for editing
    astroid field.
    """
    @property
    def value(self):
        raise NotImplementedError()

    def __init__(self,
                 parent_node: astroid.NodeNG,
                 fieldname: str):
        self.parent = parent_node
        self.fieldname = fieldname

class ListItemEditor(AbstractEditor):
    """
    Allows for the editing of features in an astroid list.
    Syncronized. Any changes in underying list are reflected in editor
    Traversable. next and previous methods allow traveling through list.
    """
    @property
    def _lst(self)->List[Any]:
        return getattr(self.parent, self.fieldname)
    @property
    def index(self)->int:
        """Gets the index of value"""
        return self._lst.index(self.value)
    @property
    def value(self)->Any:
        return self.value
    @value.setter
    def value(self, value):
        lst = self._lst
        lst[self.index] = value
    #Utilities
    def insert_before(self, value: Any):
        """Insert immediately before"""
        lst = self._lst
        lst.insert(self.index, value)
    def insert_after(self, value: Any):
        """Insert immediately after"""
        lst = self._lst
        lst.insert(self.index+1, value)
    def next(self):
        """Proceed to the next thing in this list"""
        if self.index == len(self._lst) - 1:
            raise StopIteration("End of list reached")
        self._value = self._lst[self.index+1]
    def previous(self):
        """Proceed to the previous thing in this list"""
        if self.index == 0:
            raise StopIteration("Already at the front of the list")
        self._value = self._lst[self.index-1]
    def __init__(self,
                 parent: astroid.NodeNG,
                 fieldname: str,
                 value: Any
                 ):
        self._value = value
        super().__init__(parent, fieldname)



class ListEditor(AbstractEditor):
    """
    A representation of a list.

    Appending and indexing are the only
    legal actions which may be undertaken
    from this class.

    Indexing, however, returns a item
    editor, which will allow insertion before,
    insertion after, replacing, and more.
    """
    @property
    def value(self)->List[Any]:
        return self._value
    def __getitem__(self, index: int):
        return ListItemEditor(
            self.parent,
            self.fieldname,
            self.value[index]
        )
    def __iter__(self)->Generator[ListItemEditor, None, None]:
        """
        Yields each item in the list under edit, in order.
        Edits made to the list as the iterator is traversing are ignored.
        Subsequent iterations will reflect updates.
        """
        yielding_list = self.value.copy()
        for item in yielding_list:
            yield ListItemEditor(self.parent, self.fieldname, item)
    def append(self, value: Any):
        if isinstance(value, astroid.NodeNG):
            value.parent = self.parent
        self.value.append(value)
    def __init__(self,
                 parent: astroid.NodeNG,
                 fieldname: str,
                 value: List[Any]
                 ):
        super().__init__(parent, fieldname)
        self._value = value
        self._generator_callbacks = []



class FieldEditor(AbstractEditor):
    """
    Edits a field which can be set directly.

    Two cases must be dealt with. These are
    direct nodes, and list datastructures.

    Accessing fields named these
    lead to the creation of
    """
    @property
    def value(self)->Any:
        self._value = getattr(self.parent, self.fieldname)
        if isinstance(self._value, list):
            return ListEditor(self.parent, self.fieldname, self._value)
        return self._value
    @value.setter
    def value(self, value: Any):
        assert not isinstance(self.value, list), "Perform edits through the list editor"
        self._value = value
        setattr(self.parent, self.fieldname, self.value)
    def __init__(self,
                 parent: astroid.NodeNG,
                 fieldname: str,
                 value: Any
                 ):
        super().__init__(parent, fieldname, value)

