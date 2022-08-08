"""

Transforms perform needed modifications within
the broader context of the model. They
are capable of performing a variety of neat tricks.

They operate per module, and are fed the module pipeline,
the top level tree, and the current node.

"""
import astroid
from typing import Callable, List, Tuple




def walk(node: astroid.NodeNG, root: astroid.Module, **kwargs):
    """

    Continues walking when we are certain there is nothing
    else to be worried about.

    :param node:
    :param root:
    :param pipeline:
    :param kwargs:
    :return:
    """
    output = []


