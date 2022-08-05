import inspect
import torch

from torch._sources import get_source_lines_and_file
from src import errors
from src import rcb
from src import file_builder

def test_source():
    will_fail()
    print("hello world")

sourcelines, lineno, filename = get_source_lines_and_file(test_source)
source = "".join(sourcelines)
context = errors.Context(source, filename, lineno, leading_whitespace=0, uses_true_div=True, funcname=None)
r = context.make_range(1, 3, 7)
raise errors.PreprocessingError(r, "This is a test")