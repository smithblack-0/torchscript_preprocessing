"""

This module contains utilities for sanely examining
and editing the backend astroid node database representing
the code.

One may, by a variety of methods, instance
an editor to begin working on an astroid tree.
At this point, one may iterate through the node's
children, each of which will also result in an editor,
and make changes to them.

Existing astroid methods, such as inferral, also exist.
These methods when accessed will, again, yield node
editors.

For ease of usage, it is the case that editors can accept astroid nodes to
replace, along with in some cases literals.

* NodeEditor class. Initialized with entire tree. Iterates children. Returns editors
* FieldEditer class. Initialized with an astroid field and parent.
* ListEditor class. Initialialized with a field list. Knows how to make some changes
* ListItemEditor class. Initialized from a ListEditor. Knows how to insert before and after

* AstroidItem. A representation of an astroid node. Knows how to infer. Knows how to make a node editor.
* LiteralItem
"""
import copy

import astroid
from typing import List, Any, Dict, Tuple, Type, Union, Optional, Generator

from src.build import DoubleLinkedList

### Define interface

class AbstractEditor():
    """
    Abstract class for editing
    astroid field.
    """


class AbstractFieldEditor(AbstractEditor):
    """
    Abstract class. Represents a field. Knows
    how to edit it.
    """
    def replace(self, value: Any):
        raise NotImplementedError()
    def __init__(self):
        pass


class AbstractTreeNode(AbstractEditor):
    """
    Abstract. Represents features available when
    dealing with tree nodes.
    """
    def iterate_fields(self)->AbstractFieldEditor:
        raise NotImplementedError()
    def iterate_children(self)->AbstractEditor:
        raise NotImplementedError()
    def infer(self)->"AbstractTreeNode":
        raise NotImplementedError()
    def __init__(self):
        pass

class AbstractListItem():
    """
    Represents an item in some sort of list.

    Contains methods which are usable for
    manipulating this this item - replacing,
    placing before, placing after.

    """
    @property
    def index(self)->int:
        """Gets the index of this item in the list"""
        return self.editor.index(self)
    def insert_before(self, value: any):
        """Inserts before an item in the list"""
        self.editor.insert(self.index, value)
    def insert_after(self, value):
        """Inserts after an itme in the list"""
        self.editor.insert(self.index+1, value)
    def next(self)->"ListItem":
        if len(self.editor) == (self.index - 1):
            raise StopIteration("At end of list")
        return self.editor[self.index+1]
    def previous(self)->"ListItem":
        if self.index == 0:
            raise StopIteration("Cannot get previous: already at start of list")
        return self.editor[self.index -1]
    def __init__(self,
                 item_value: Any,
                 item_id: Any,
                 list_editor: "AbstractListEditor"):
        self.value = item_value
        self.editor = list_editor
        self.id = item_id



class AbstractListEditor():
    def index(self, item: object)->int:
        """
        Index an item.
        Should be Listitem independent, and
        work regardless of being handed an AbstractListItem or
        a raw item
        """
        raise NotImplementedError()
    def append(self, value):
        """
        Append an itme ot a list. Should work
        with listitems and raw types.
        """
        raise NotImplementedError()
    def insert(self, index: int, value: AbstractListItem):
        """
        Insert an item into a list

        Should work with list items and raw types.
        """
        raise NotImplementedError()
    def __str__(self):
        raise NotImplementedError()
    def __len__(self):
        raise NotImplementedError()
    def __getitem__(self,
                    key: Union[slice, int])->Union["AbstractListEditor", AbstractListItem]:
        raise NotImplementedError()
    def __setitem__(self,
                    key: Union[slice, int, AbstractListItem],
                    value: AbstractListItem):
        raise NotImplementedError()


class AbstractListItem():
    """
    Abstract feature representing the interface
    """


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



