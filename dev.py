import importlib
import sys
from importlib.machinery import ModuleSpec
from typing import Sequence, Optional,

print(sys.meta_path)

class tempcodeMockfinder(importlib.abc.MetaPathFinder):
    def find_spec(self,
                  fullname,
                  path,
                  target=None) -> Optional[ModuleSpec]:
        print(fullname, path, target)
        return None
class MyLoader(importlib.abc.Loader):
    def exec_module(self, module):
        print(module)
        exec(module)

if tempcodeMockfinder in sys.meta_path:
    index = sys.meta_path.index(tempcodeMockfinder)
    sys.meta_path.pop(index)
sys.meta_path.append(tempcodeMockfinder)

import torch
import thingy as item