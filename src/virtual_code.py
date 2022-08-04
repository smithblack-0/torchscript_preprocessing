"""
This module manages the creation and usage
of virtual code. Virtual code uses some
tricks of the import system to ensure
inspect is adequetely redirected into the
code that is being created.
"""
from importlib.machinery import ModuleSpec
from typing import Callable, Any, Dict, Optional
import importlib
from importlib import util
import random
import rcb

class mockModuleLoader(importlib.abc.InspectLoader):
    """
    Loads the virtual module, and
    returns features from it.
    """
    def __init__(self, source: str, env: rcb.EnvProxy):
        self.source = source
        self.env = env
    def create_module(self, spec: ModuleSpec):
        return None
    def get_source(self, fullname: str):
        return self.source
    def exec_module(self, module):
        print(module)
        exec(self.source, self.env.locals, self.env.globals)
        print(self.env.locals)
        print(self.env.globals)
        print(potato)
        return module

source = """\
print(random.randint(0, 5))

print("hello world")
potato = 3
"""
proxy = rcb.makeEnvFromFrame()
loader = mockModuleLoader(source, proxy)
spec = ModuleSpec("test", loader)
spec =  util.spec_from_loader("test", loader)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print(dir(module))
