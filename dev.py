from typing import Optional
import importlib
from importlib import util
from temp import envtemp
from importlib.machinery import ModuleSpec
import inspect


class VirtualFile(importlib.abc.InspectLoader):
    def __init__(self, source: str, environment: envtemp.EnvProxy):
        self.source = source
        self.environment = environment
    def get_source(self, fullname: str) -> Optional[str]:
        return self.source
    def exec_module(self, module):
        sandbox_env = self.environment.__copy__()
        exec(self.source, sandbox_env.locals, sandbox_env.globals)

        novel = {key: value for key, value in sandbox_env.formatted_dict().items()
                 if value not in self.environment.formatted_dict().values()}
        for key, value in novel.items():
            setattr(module, key, value)

testsource = """

def apple():
\tprint("boop")

raise Exception()

"""
env = envtemp.EnvProxy(locals(), globals())
file = VirtualFile(testsource, env)

spec = util.spec_from_loader("temp", file)
module = util.module_from_spec(spec)
module.__file__ = "virtual"
print(vars(module))
spec.loader.exec_module(module)

print(vars(module))