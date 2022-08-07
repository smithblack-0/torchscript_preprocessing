"""
Test features to check the ability of the context
redirector to do its job.
"""
import inspect
import unittest
from typing import List

import torch
from src import context
from src import datastructures
from src import errors
from src import rcb
from torch import _sources

#Make source content
def source1():
    print("hello world")
def source2():
    item = 3
    return item
def source3(item):
    """docstring"""
    return item
basic_source = [source1, source2, source3]

#Make passing torch content
def source4():
    return 3
def source5(item: torch.Tensor):
    """"""
    return item + 4
def source6(items: List[torch.Tensor]):
    output = 0
    for item in items:
        output += item.sum()
    return output
torch_source = [source4, source5, source6]
#Make failing torch content
def source7(item):
    item.append(3)
    return item
torch_fail = [source7]



#Run tests
class test_Context(unittest.TestCase):
    """
    Test feature for the context object.

    Performs both unit tests, along with
    torch integration tests.
    """
    def create_codeblock(self, obj):
        sourcelines, lineno, filename = _sources.get_source_lines_and_file(obj)
        source = "".join(sourcelines)
        context = _sources.SourceContext(source, filename, lineno, 0)

    def setUp(self) -> None:




        _sources.SourceContext()

        codeblocks = []
        codeblocks.append(datastructures.CodeBlock())
    def test_creation(self):
        """ Tests whether or not we can create anything at all"""

        env = rcb.makeEnvFromFrame()
        path = inspect.currentframe().f_code.co_filename


        context.Context()
        pass
    def test_basic_execution(self):
        """ Tests whether or not we can sanely execute and retriev code"""
        pass
    def test_torchscript_execution(self):
        """Test whether or not we can compile then retrieve objects from context"""
        pass
    def test_torcherror_redirection(self):
        """Test whether or not the unit is capable of redirecting a torchscript err"""
        pass
    def test_self_redirection(self):
        """Test whether or not the module will redirect errors it itself generated"""
        pass