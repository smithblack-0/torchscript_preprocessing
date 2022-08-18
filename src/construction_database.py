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
import copy
import inspect

import astroid
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, Type, List, Tuple, Callable, Generator


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
    depth: int
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
    def child(self) -> Optional["BuildNode"]:
        return self._child

    @child.setter
    def child(self, value: Optional["BuildNode"]):
        if self.child is not value:
            if self._child is not None:
                # Release current next node
                self._child._parent = None
            self._child = value
            self._child.parent = self

    @property
    def parent(self) -> Optional["BuildNode"]:
        return self._parent

    @parent.setter
    def parent(self, value: Optional["BuildNode"]):
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

    def append(self, value: "BuildNode"):
        """Appends a value to the end of the linked list"""
        last = self.last
        value.parent = last
        last.child = value

    def insert(self, value: "BuildNode"):
        """Inserts node in front of current entry"""
        parents_new_child = value.first
        my_new_parent = value.last
        self.parent.child = parents_new_child
        self.parent = my_new_parent
    def __iter__(self)-> "BuildNode":
        yield self
        node = self
        while node.next is not None:
            node = node.next
            yield node

    def __init__(self,
                 child: Optional["BuildNode"] = None,
                 parent: Optional["BuildNode"] = None):
        self._child = child
        self._parent = parent


class BuildNode(DoubleLinkedList):
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

    tree_descent = False
    tree_ascend = False
    subclass_registry = {}

    def __init_subclass__(cls, **kwargs):
        """Registers subclasses to the registry when they are created"""
        assert "registry_name" in kwargs, "keyword argument 'registry_name' not passed to class on creation"
        registry_name = kwargs["registry_name"]
        assert registry_name in ActionOptionsEnum, "Ensure you place this in enum too when extending the code"
        cls.subclass_registry[registry_name] = cls

    def create(self, field_name: str, node_type: Type[astroid.NodeNG]):
        """Returns a creation node, as the next node in the linked list"""
        cls: Type["CreateTreenodeAction"] = self.subclass_registry[ActionOptionsEnum.CreateTreeNode]
        self.append(cls(field_name=field_name, node_type=node_type))
    def commit(self):
        """Returns an emplacement node, as the next node in the linked list"""
        cls: Type["CommitTreeBuildNode"] = self.subclass_registry[ActionOptionsEnum.CommitTreeNode]
        self.append(cls())
    def emplace(self, field_name: str, literal: Any):
        """Returns a build node, as the next node in the linked list"""
        cls: Type["EmplaceLiteral"] = self.subclass_registry[ActionOptionsEnum.EmplaceLiteral]
        self.append(cls(field_name=field_name, literal=literal))

    #Execution engine
    def execute(self)->astroid.NodeNG:
        """Runs all the nodes. Returns the result"""
        #Basically, this runs the elements of the
        #list in sequence to generate a decent node.
        depth = 0
        ast_node = None
        stack = []
        for action_node in self:
            if action_node.tree_descent:
                depth += 1
            if action_node.tree_ascent:
                depth -= 1
            ast_node = self.action(ast_node, stack)
            if depth <= 0:
                return ast_node

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
    def edit(self, node: astroid.NodeNG)-> "BuildNode":
        """
        Will seek out and return the linked list node
        location associated with creating this astroid node.
        """
        start = self.first
        assert hasattr(node, "_created")
        for action_node in start:
            # noinspection PyUnresolvedReferences
            if action_node is node._created:
                return action_node


    def revert(self, node)-> "BuildNode":
        """
        Will revert the linked list to
        this node in the build process,
        dumping the rest. Returns
        the new list.
        """
        dump_from_this_node = self.edit(node)
        dump_from_this_node.child = None
        return dump_from_this_node.first

    def copy(self)-> "BuildNode":
        return copy.deepcopy(self)

    def __init__(self,
                 child: Optional["BuildNode"] = None,
                 parent: Optional["BuildNode"] = None):
        super().__init__(child, parent)


class CreateTreenodeAction(BuildNode, registry_name = ActionOptionsEnum.CreateTreeNode):
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

    tree_descent = True
    def action(self, node: Optional[astroid.NodeNG], stack: List[context]) ->astroid.NodeNG:
        """Creates a node, attached to the given parent"""
        if isinstance(getattr(node, self.field_name), list):
            is_list = True
        else:
            is_list = False
        node._created = self #Allows retrieval by editing engine.
        if len(stack) > 0:
            depth = stack[-1].depth + 1
        else:
            depth = 0
        ctx = context(node,
                      is_tree_create = True,
                      field_name=self.field_name,
                      depth=depth)
        stack.append(ctx)
        node = self.cls(parent=node)
        return node
    def __init__(self,
                 field_name: str,
                 node_type: Type[astroid.NodeNG],
                 child: Optional["BuildNode"]=None,
                 parent: Optional["BuildNode"]=None):
        super().__init__(child, parent)
        self.field_name = field_name
        self.cls = node_type

class CommitTreeBuildNode(BuildNode, registry_name=ActionOptionsEnum.CommitTreeNode):
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

    tree_ascend = True
    def action(self, node: Optional[astroid.NodeNG], stack: List[context]) ->astroid.NodeNG:
        ctx = stack.pop()
        parent = ctx.node
        field_name = ctx.field_name

        assert ctx.is_tree_create, "Did not use all context first" #TODO - more descritive
        place_child_onto_parent(parent, node, field_name)
        return parent
    def __init__(self,
                 child: Optional["BuildNode"]=None,
                 parent: Optional["BuildNode"]=None):
        super().__init__(child, parent)


class EmplaceLiteral(BuildNode, registry_name=ActionOptionsEnum.EmplaceLiteral):
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
                 child: Optional["BuildNode"]=None,
                 parent: Optional["BuildNode"]=None):
        super().__init__(child, parent)
        self.field_name = field_name
        self.literal = literal

class FieldEditor():
    """
    This class is generated wherever a node is
    detected. It, in turn, has methods which
    can place a node into this spot.
    """

    def __init__(self,
                 parent: BuildNode,
                 node: Any,
                 field_name: str,
                 field_type: Type[Any],):
        self.node = node
        self.parent = parent
        self.field_name = field_name
        self.field_type = field_type
    def insert(self):
        """Inserts to a position which is immediately prior. Not valid for lists."""
    def append(self):
        """ Append current node to indicated feature. Only works for lists"""
        assert issubclass(self.field_type, list)

    def set(self):
        """Sets current node to field. Not valid for lists"""
    def emplace(self):
        """Places node back at the same position it was found in"""


class NodeIterator():


class NodeBuilder():
    """
    This will iterate over
    a astroid tree, yielding
    a sequence of node builders
    all the while.

    Once iteration is finished, the
    last entry will be an astroid node.
    """
    def __iter__(self):
        builder = BuildNode()
    def __init__(self, obj: object):
        source = inspect.getsource(obj)
        tree = astroid.parse(source)



def rebuild(obj: object, transforms: List[Callable[[BuildNode, astroid.NodeNG], BuildNode]]):
    #Making the project in a broader source context
    Builder = BuildNode()
    target_source = inspect.getsource(obj)
    module_source = inspect.getsource(inspect.getmodule(obj))


    #Traverse tree, traveling to the edit site and building a nodebuilder context
    #along the way.
    Stack: List[Tuple[Generator[astroid.NodeNG, None, None], astroid.NodeNG]] = []

    current_working_node = astroid.parse(module_source)
    working_node_subchildren_generator = current_working_node.get_children()
    while True:
        if current_working_node.as_string() == target_source:
            break
        try:
            child: astroid.NodeNG = next(working_node_subchildren_generator)
            field_name = current_working_node.locate_child(child)
            if isinstance(child, astroid.NodeNG):
                Builder.create(current_working_node.locate_child(child), type(child))
                Stack.append((working_node_subchildren_generator, current_working_node))
                current_working_node = child
                working_node_subchildren_generator = current_working_node.get_children()
            else:
                Builder.emplace(field_name, child)
        except StopIteration:
            if len(Stack) == 0:
                raise RuntimeError("Target source never found")
            Builder.commit()
            working_node_subchildren_generator, current_working_node = Stack.pop()

    #Traverse the tree among the code we care about.
    #
    Stack: List[Tuple[Generator[astroid.NodeNG, None, None], astroid.NodeNG]] = []
    working_node_subchildren_generator = current_working_node.get_children()
    while True:
        if current_working_node.as_string() == target_source:
            break
        try:
            child = next(working_node_subchildren_generator)
            field_name = current_working_node.locate_child(child)
            if isinstance(child, astroid.NodeNG):
                Builder.create(current_working_node.locate_child(child), type(child))
                Stack.append((working_node_subchildren_generator, current_working_node))
                current_working_node = child
                working_node_subchildren_generator = current_working_node.get_children()
            else:
                Builder.emplace(field_name, child)
        except StopIteration:
            if len(Stack) == 0:
                return Builder.execute()
            child = current_working_node
            for transform in transforms:
                transform(Builder, child)
            Builder.commit()
            working_node_subchildren_generator, current_working_node = Stack.pop()
    raise Exception()
