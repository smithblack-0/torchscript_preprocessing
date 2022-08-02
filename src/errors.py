"""
This module manages creating and
providing methods for errors.

It draws heavily from torch.
"""
from typing import Optional

import torch
from torch.jit.frontend import FrontendError
from torch._sources import SourceContext

class Context(SourceContext):
    """
    A strongly typed version of the context

    Used to report where an error is coming from
    """
    def __init__(self,
                 source: str,
                 filename: str,
                 file_lineno: int,
                 leading_whitespace: int,
                 uses_true_div: bool = False,
                 funcname: Optional[str] = None):
        super().__init__(source, filename, file_lineno,
                         leading_whitespace, uses_true_div, funcname)


class PreprocessingError(FrontendError):
    """
    The error class. Contains information
    on where in the code things have gone wrong
    """
    def __init__(self, source_range, msg):
        self.source_range = source_range
        self.msg = msg

        # This has to be instantiated here so the ErrorReport is accurate to the
        # call stack when the FrontendError was raised
        self.error_report = torch._C.ErrorReport(self.source_range)

    def __str__(self):
        return self.msg + self.error_report.what().lstrip()

