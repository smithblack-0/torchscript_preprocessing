from __future__ import annotations

import copy

import astroid
from typing import List, Tuple, Optional


class Transform():
    """

    A transform accepts a astroid node and an astroid tree, and
    processes and returns a node and tree. This repeats
    for all subsequent transforms.

    - The node returned may not belong to the original tree.
    - Any modifications to the wider tree should create a new tree
    - A few methods exist to make life easier
    """

    def __init__(self):
        pass
    def __call__(self, node: astroid.NodeNG, processor: Processor):
        raise NotImplementedError()



class Processor():
    """

    A processer applies a sequence of transforms to a node, then
    returns the result. It is present in every transform, and as
    a result also contains quite a few utility methods. It should be
    noted that these methods will generally return a new tree when
    edited.

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
                        spaces: int = 0) -> Tuple[astroid.NodeNG, astroid.NodeNG]:
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
        return node, to_insert[0]

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

    def __init__(self, transforms: List[Transform]):
        self.transforms = transforms
    def __call__(self,
                 node: astroid.NodeNG
                 ) -> astroid.NodeNG:
        for transform in self.transforms:
            node = transform(node, self)
        return node
