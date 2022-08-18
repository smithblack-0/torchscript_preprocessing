"""
This module is responsible for implimenting
the various kinds of actions a linked list
history node may perform.

A linked list is used, to ensure that any edits
on earlier nodes in the chain immediately
is reflected elsewhere as well

Nodes are created by first Creating a template
to fill in, then Emplacing details onto them, and
finally Closing the template out.
"""
import astroid
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, Type, List, Tuple

def place_child_onto_parent(parent: astroid.NodeNG, child: Any, fieldname: str):
    """Places a node onto another node at the given fieldname"""
    #### Warning - side effects ###
    field = getattr(parent, fieldname)
    if isinstance(field, list):
        field.append(child)
    else:
        setattr(parent, fieldname, child)


class ActionOptionsEnum(Enum):
    Start = "Start"
    CreateTreeNode = "CreateTreeNode"
    EmplaceLiteral = "CreateLiteral"
    CommitTreeNode = "CommitTreeNode"

@dataclass
class context:
    """
    A context class. Exists to give a convenient place
    to push information that is needed later. Extend
    this if you need a custom function.
    """


    node: astroid.NodeNG
    is_tree_create: bool = False
    field_name: Optional[str] = None

class DoubleLinkedList():
    """
    A class for supporting doubly linked list
    """

    # Linked list logic
    #
    # Linked lists can be a bit tricky
    # to get right. As a result, we isolate
    # the logic itself in it's own class,
    # to be inherited from, so that the
    # unit tests can be performed on it with
    # ease
    #
    @property
    def child(self) -> Optional["ActionLinkNode"]:
        return self._child

    @child.setter
    def child(self, value: Optional["ActionLinkNode"]):
        if self.child is not value:
            if self._child is not None:
                # Release current next node
                self._child._parent = None
            self._child = value
            self._child.parent = self

    @property
    def parent(self) -> Optional["ActionLinkNode"]:
        return self._parent

    @parent.setter
    def parent(self, value: Optional["ActionLinkNode"]):
        if self._parent is not value:
            if self._parent is not None:
                # Release current next node
                self._parent._child = None
            self._parent = value
            self._parent._child = self
    @property
    def first(self):
        if self.parent is None:
            return self
        return self.parent.first
    @property
    def last(self):
        if self.child is None:
            return self
        return self.child.last

    def insert(self, value: "ActionLinkNode"):
        """Inserts node in front of current entry. Insertion begins from first node, to last node"""
        parents_new_child = value.first
        my_new_parent = value.last
        self.parent.child = parents_new_child
        self.parent = my_new_parent

    def __init__(self,
                 child: Optional["ActionLinkNode"] = None,
                 parent: Optional["ActionLinkNode"] = None):
        self._child = child
        self._parent = parent


class ActionLinkNode(DoubleLinkedList):
    """
    A generic action node

    Contains definitions for interface,
    along with a registry for keeping the
    various subclasses in

    Also contains methods and properties
    for supporting a linked list structure.
    """

    #### Concept ###
    #
    # The basic idea here is that these nodes will
    # form a linked list which, one item at a time,
    # performs the method called "action" in sequence
    # while traveling along the list. Each action can
    # thus be viewed as performing a transform on
    # the node, and on the actions, then passing
    # those features into the next action in the chain

    #### Building tools ###
    #
    # The features below come in a few different flavors. First,
    # there are the creation utilities. The first features of
    # node are the actions registry
    #
    # Any time this class is subclassed, the class will be put
    # into the subclass registry with the given registry name.
    # Functions in the class, such as create and emplace, are
    # then able to use these registry names to create appropriate
    # nodes. To keep everything nicely syncronized, we use an Enum
    #
    # Second is the execute and action blocks. An action is conceptually
    # something that will be done to an incoming ast node in a chain
    # in order to build a appropriate tree. The two things that
    # exist in the action, going into it, are the stack and the node
    # The node is whatever popped out of the previous action. The stack,
    # meanwhile, is a place persistant information can be shoved if
    # needed as a context dataclass.
    #
    # The context dataclass is extendable if more information is needed
    # for future maintainers. Just ensure an appropriate "is_{blank}" statement
    # exists


    subclass_registry = {}
    def __init_subclass__(cls, **kwargs):
        """Registers subclasses to the registry when they are created"""
        assert "registry_name" in kwargs, "keyword argument 'registry_name' not passed to class on creation"
        registry_name = kwargs["registry_name"]
        assert registry_name in ActionOptionsEnum, "Ensure you place this in enum too when extending the code"
        cls.subclass_registry[registry_name] = cls


    def action(self,
               node: Optional[astroid.NodeNG], stack: List[context]
               ) -> astroid.NodeNG:
        """
        The primary feature. Must be set by the subclass
        :param node: A astroid node, or possibly none if just starting
        :param stack: A space in which one can store context
        :return: A astroid node, representing what we are currently working with
        """
        raise NotImplementedError("Should not directly use")

    #Editing engine
    def edit(self, node: astroid.NodeNG):
        """
        Will seek out and return the linked list node
        associated with creating this astroid node.

        Allows easy editing.
        """


    def __init__(self,
                 child: Optional["ActionLinkNode"] = None,
                 parent: Optional["ActionLinkNode"] = None):
        super().__init__(child, parent)

class CreateTreenodeAction(ActionLinkNode, registry_name = ActionOptionsEnum.CreateTreeNode):
    """
    A creation node. A part of a larger linked list

    This is responsible for creating a subsection of
    a ast tree. It will create a node of the given
    type on demand from elsewhere in the linked list.

    When the node is being created, we must provide
    the relevant field information so we can make
    a context packet.
    """
    #### Concept ####
    #
    # This basically shoves the current state into a context
    # dataclass, then starts a new node of the demanded
    # type when called.


    def action(self, node: Optional[astroid.NodeNG], stack: List[context]) ->astroid.NodeNG:
        """Creates a node, attached to the given parent"""
        if isinstance(getattr(node, self.field_name), list):
            is_list = True
        else:
            is_list = False
        node._created = self #Allows retrieval by editing engine.
        ctx = context(node, is_tree_create = True, field_name=self.field_name)
        stack.append(ctx)
        node = self.cls(parent=node)
        return node
    def __init__(self,
                 field_name: str,
                 node_type: Type[astroid.NodeNG],
                 child: Optional["ActionLinkNode"]=None,
                 parent: Optional["ActionLinkNode"]=None):
        super().__init__(child, parent)
        self.field_name = field_name
        self.cls = node_type

class CommitTreeNode(ActionLinkNode, registry_name=ActionOptionsEnum.CommitTreeNode):
    """
    A node for committing a piece of node
    information to a particular point in the
    tree

    After this runs, one ends up looking at the
    prior node during the next action.
    """
    ### Concept ###
    # This basically just removes the last state from the
    # stack, then attaches the current node, which is
    # now finished, to it.


    def action(self, node: Optional[astroid.NodeNG], stack: List[context]) ->astroid.NodeNG:
        ctx = stack.pop()
        parent = ctx.node
        field_name = ctx.field_name

        assert ctx.is_tree_create, "Did not use all context first" #TODO - more descritive
        place_child_onto_parent(parent, node, field_name)
        return parent
    def __init__(self,
                 child: Optional["ActionLinkNode"]=None,
                 parent: Optional["ActionLinkNode"]=None):
        super().__init__(child, parent)


class EmplaceLiteral(ActionLinkNode, registry_name=ActionOptionsEnum.EmplaceLiteral):
    """
    A node for placing literals into the tree
    network. Provide with a literal and a field
    name.

    This places a literal onto the passed node
    with no context creation or deletion.
    """
    def action(self, node: Optional[astroid.NodeNG], stack: List[context]) ->astroid.NodeNG:
        place_child_onto_parent(node, self.literal, self.field_name)
        return node
    def __init__(self,
                 field_name: str,
                 literal: Any,
                 child: Optional["ActionLinkNode"]=None,
                 parent: Optional["ActionLinkNode"]=None):
        super().__init__(child, parent)
        self.field_name = field_name
        self.literal = literal

class ActionBuilder()
