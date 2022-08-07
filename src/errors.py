"""
This module manages creating and
providing methods for errors.

It draws heavily from torch.
"""
from typing import Optional, List, Any, Union

from torch._C._jit_tree_views import SourceRange
from torch.jit.frontend import FrontendError, NotSupportedError, UnsupportedNodeError
from typing import Callable


class UnhandledPreprocessingError(Exception):
    @staticmethod
    def precompile(msg: str)->Callable[[Any], "UnhandledPreprocessingError"]:
        def callback(tb):
            return UnhandledPreprocessingError(tb, msg)
        return callback
    def __init__(self, tb: Any, message: str):
        self.tb = tb
        super().__init__(message)

class TorchParseError(FrontendError):
    @staticmethod
    def precompile(source_range: SourceRange, activity: str) ->Callable[[Any], "TorchParseError"]:
        """Precompiles everything into a callback that just needs the tb"""
        def callback(tb):
            return TorchParseError(source_range, activity, tb)
        return callback
    def __init__(self, source_range: SourceRange, activity: str, tb):
        msg = "torch scripting error encountered while preprocessing code for {activity}".format(activity=activity)
        self.tb = tb
        super().__init__(source_range=source_range, msg=msg)


Types = Union[UnhandledPreprocessingError, TorchParseError]