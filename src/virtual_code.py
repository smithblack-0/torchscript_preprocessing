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
from importlib import Mod

class codeFinder(importlib.abc.MetaPathFinder):
    def find_spec(
        self,
        fullname: str,
        path,
        target
    ) -> Optional[ModuleSpec]:


class TempCode():
    """
    A temporary code management
    objects.

    This consists of a file in
    which it is the case that
    code may be appended.
    """
