import inspect
import torch

from torch._sources import get_source_lines_and_file
from src import errors
from src import rcb
from src import file_builder

def test_sources():
       print("hello world")

sourcelines, lineno, filename = get_source_lines_and_file(test_sources)
source = "".join(sourcelines)
context = errors.Context(source, filename, lineno, leading_whitespace=0, uses_true_div=True, funcname=None)
r = context.make_range(1, 3, 7)
try:
    raise errors.PreprocessingError(r, "This is a test")
except Exception as err:
    r = err.args[0]
    path = r.__str__()

    print(r.__repr__())
    print(r.__str__())
    print(r.start)
    print(r.end)
    print(r.highlight())
    report = torch._C.ErrorReport(r)

    print(report.call_stack())
    print(report.what())
    print(dir(r))
