from typing import *
import transforms
import astroid
import inspect
import torch
from torch.jit import frontend
from torch import _jit_internal
from torch.jit.frontend import ClassDef
from main import other



class inherit(other):
    callback = _jit_internal.createResolutionCallbackFromFrame(1)

item = frontend.get_jit_class_def(inherit, 'self')
print(dir(item))
print(item)
