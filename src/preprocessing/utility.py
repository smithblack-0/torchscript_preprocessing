"""

Contains functions which are utilized
for preprocessing, for whatever purpose

"""

import astroid
import inspect
from typing import Union, Type, Optional

from torch._sources import get_source_lines_and_file
from torch._sources import make_source_context






def parse(obj: object):
    """
    Parses the ast tree for an object.

    Attatches features "parent", "prior", "next"

    These respectively represent a link to the
    parent, the prior node during a depth first
    traversal, and the next node in a depth
    first traversal

    :param obj:
    :return:
    """
