"""

This module is responsible for handling
the generation and modification of torch's resolution
callbacks.

We use the same logic torch does, except
it is the case our resolution callbacks
can act as a proxy, referncing functions
elsewhere in our particular environment

"""
import builtins
import inspect
from typing import Dict, Any, Callable
from torch import _jit_internal

class EnvProxy(object):
    """
    The environmental proxy object.
    """
    def __init__(self,
                 f_locals: Dict[str, Any],
                 f_globals: Dict[str, Any],
                 f_builtins: Dict[str, Any]):
        self.locals = f_locals.copy()
        self.globals = f_globals.copy()
        self.builtins = f_builtins.copy()
    def __getattr__(self, key):
        if key in self.locals:
            return self.locals[key]
        elif key in self.globals:
            return self.globals[key]
        elif key in dir(self.builtins):
            return getattr(self.builtins, key)

def makeEnvFromFrame(frames_up: int = 0)-> EnvProxy:
    """
    Makes an editable env from a frame.

    Copied more or less from torch.

    :param frames_up: How many frames to ascend before making
    :return: A EnvProxy object
    """
    frame = inspect.currentframe()
    i = 0
    while i < frames_up + 1:
        assert frame is not None
        frame = frame.f_back
        i += 1

    assert frame is not None
    f_locals = frame.f_locals
    f_globals = frame.f_globals
    f_builtins = {key : getattr(builtins, key) for key in dir(builtins)}
    return EnvProxy(f_locals, f_globals, f_builtins)

def createCallbackfromEnv(env: EnvProxy)->Callable[[str], Any]:
    """
    Creates the actual callback from the
    env proxy object

    :param env:
    :return:
    """
    return _jit_internal.createResolutionCallbackFromEnv(env)