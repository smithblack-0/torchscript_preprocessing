from __future__ import annotations

import copy

import astroid
from typing import List, Tuple, Optional
from torch.jit.frontend import UnsupportedNodeError
from torch.jit.frontend import make_source_context
#Make source context(source, filename, file_lineno, leading_whitespace_len, uses_true_division, funcname)

class Transform():
    """

    A transform is a logic unit of the preprocessing
    system. It is the case that an individual transform
    operates by accepting a node, processing the node, then
    calling the appropriate part of the processor for the situation.

    A transform is expected to return two items. The first will
    be a node, presumed to be the location on which to next
    perform processing. This could either be the unchanged current
    node, or a new node. The second is a bool. It should be true
    if the tree was modified, and false otherwise.

    """
    def get_ancestor_from_top(self, node: astroid.NodeNG, depth: int) -> Optional[astroid.NodeNG]:
        """

        For a given node, gets the nth ancestor, as
        measured from the top level ancestor

        Returns None if not available. No modifications

        :param node: The node to query from
        :param depth: How deep into the top to go
        :return: The Nth ancestor, or None if not available
        """

        ancestors = list(node.node_ancestors())
        ancestors.reverse()
        if len(ancestors) < depth:
            return None
        return ancestors[depth]

    @staticmethod
    def insert_sibling_in_front(
                        node: astroid.NodeNG,
                        to_insert: List[astroid.NodeNG],
                        spaces: int = 0) -> astroid.NodeNG:
        """

        This function will start at a given node, then move up the
        tree until finding the first parent with a code block. Once
        there, it will insert the to_insert nodes "spaces" in front
        of the current parent node.

        A new tree is built by this method, and the return is the
        last node examined, and the root of the new tree.

        :param node: The node to insert in front of
        :param to_insert: A list of nodes to insert
        :param spaces: How many spaces in front to begin the insertion. 0 is right in front.
        :return: The node, and the first inserted node.
        :raise: AssertionError, if the parent node is not a code block.
        """

        assert hasattr(node.parent, 'body'), "Cannot insert if prior node is not a code block"
        node = copy.deepcopy(node)
        to_insert = copy.deepcopy(to_insert)

        parent = node.parent
        for item in to_insert:
            item.parent = parent

        insertion_point = parent.body.index(node)
        insertion_point -= spaces
        assert insertion_point >= 0, "Attempted to insert sibling before start of list."
        parent.body = parent.body[:insertion_point] + to_insert + parent.body[insertion_point:]
        return to_insert[0]

    @staticmethod
    def insert_sibling_behind(node: astroid.NodeNG,
                              to_insert: List[astroid.NodeNG],
                              spaces: int = 0
                              )-> Tuple[astroid.NodeNG, astroid.NodeNG]:
        """

        This function will go to the parent code block, then
        A new tree is built by this method, and the return is the
        last node examined, and the root of the new tree.

        :param node: The node to insert in front of
        :param to_insert: A list of nodes to insert
        :param spaces: How many spaces in front to begin the insertion. 0 is right in front.
        :return: The node, and the first inserted node.
        :raise: AssertionError, if the parent node is not a code block.
        """

        assert hasattr(node.parent, 'body')
        node = copy.deepcopy(node)
        to_insert = copy.deepcopy(to_insert)

        parent = node.parent
        for item in to_insert:
            item.parent = parent

        insertion_point = parent.body.index(node)
        insertion_point += spaces
        assert insertion_point < len(parent.body), "Attempted to insert sibling after end of list"
        parent.body = parent.body[:insertion_point] + to_insert + parent.body[insertion_point:]
        return node, to_insert[0]
    def replace_node(self,
                     node: astroid.NodeNG,
                     replacement: astroid.NodeNG) -> astroid.NodeNG:
        """
        Replace the indicated node, with the indicated
        replacement node, while keeping everything
        decoupled.

        Return the replacement node, in a new tree.


        :param node: The node to replace
        :param replacement: The replacement node.
        :return: The replacement node, in the new tree, and the new tree.
        """
        assert hasattr(node.parent, 'body'), "Cannot replace a node not right below a code block"
        node = copy.deepcopy(node)
        replacement = copy.deepcopy(replacement)
        nodepoint = node.parent.body.index(node)

        parent = node.parent
        replacement.parent = parent
        parent.body[nodepoint] = replacement
        return replacement


    def __init__(self):
        pass
    def __call__(self, node: astroid.NodeNG, processor: Processor)-> Tuple[astroid.NodeNG, bool]:
        raise NotImplementedError()



class Processor():
    """
    An iterative tree procesor. When called,
    the internal transforms are called, one at
    a time. Each transform should return a node.

    Should the output node be the same object as
    the input node, the processor goes onto the
    next transform. Otherwise, it restarts the
    transform stack on top of the new node.

    If it should be the case that all transforms are
    exhausted, we get the next sibling to the
    given node. If it is the case that all such
    nodes are exhausted, we return the final node.
    """



    def apply_transforms(self, node: astroid.NodeNG):
        """
        Applies transforms until either
        a modification occurs, in which case
        we break and indicate, or until all
        transforms are exhausted.

        :param node:
        :return:
        """

        modified = False
        for transform in self.transforms:
            node, modified = transform(node, self)
            if modified:
                break
        return node, modified


    def __init__(self, transforms: List[Transform]):
        self.transforms = transforms
    def __call__(self, node: astroid.NodeNG):
        """
        :param node: The node to begin processing on, working our way down the page.
        :return: The root of the last node.
        """
        # Setup  the counters
        while True:
            modified = False
            child_counter = 0
            while child_counter < len(list(node.get_children())):
                update, modified = self.apply_transforms(child)
                if modified:
                    node = update
                    break
                update, modified = self(child)
                if modified:
                    node = update
                    break
            if not modified:
                print(node.as_string())
                return node, False
