"""

Just a proxy for the implimentation later.

"""


import builtins
from typing import Dict, Any


class EnvProxy(object):
    def formatted_dict(self)->Dict[str, Any]:
        """ Returns a dictionary representing the entire environment"""
        output = {}
        output.update(vars(builtins))
        output.update(self.globals)
        output.update(self.locals)
        return output
    def __copy__(self):
        return EnvProxy(self.locals.copy(), self.globals.copy())
    def __getattr__(self, key):
        if key in self.locals:
            return self.locals[key]
        elif key in self.globals:
            return self.globals[key]
        elif key in dir(builtins):
            return getattr(builtins, key)
    def __init__(self,
                 f_locals: Dict[str, Any],
                 f_globals: Dict[str, Any]):
        self.locals = f_locals
        self.globals = f_globals