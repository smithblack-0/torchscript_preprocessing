"""
This module manages the creation and usage
of virtual code. Virtual code uses some
tricks of the import system to ensure
inspect is adequetely redirected into the
code that is being created.
"""
import inspect
import os
import re
import pathlib
import tempfile
import datetime
from importlib.machinery import ModuleSpec
from typing import Callable, Any, Dict, Optional
import importlib
from importlib import util
from importlib.machinery import ModuleSpec
import random
from src import rcb


boilerplate_template="""\
\"\"\"
This is an automatically generated 
file produces by preprocessing. This
file is designed to be run within
the namespace it was called in.

Do not edit this file.

DEBUG_INFO:

This file was created from a file located at: {path}
This file was created at time: {time}

The environmental variables present 
upon creation are:

{environmentals}
\"\"\"
"""


class TempCodeFile():
    """
    A file manager for temporary
    code. Initialized with source code
    string. Cleans up after itself upon
    GC.
    """
    @property
    def name(self):
        return pathlib.Path(self.path).name
    @property
    def path(self):
        return self._path
    @property
    def contents(self)->str:
        with open(self.path) as f:
            f.seek(0)
            return f.read()
    def __init__(self, source: str):
        handle = tempfile.NamedTemporaryFile(mode="w",
                                                  suffix='.py',
                                                  delete=False)

        handle.write(source)
        self._path = handle.name
        handle.close()
        self.release = True
    def __del__(self):
        if self.release:
            os.remove(self.path)

class CodeBuilder():
    """
     A location for building temporary
     code.

     Consists of boilerplate at the front indicating
     debug information, along with methods for
     adding code blocks on.

     When provided with an environment, the contents
     are written to a temporary file, then
     loaded as a module with the
     Collects together boilerplate, along
     with code entries.

     When called with an environment, the environment
     is cloned, all code runs in the new sandbox, and
     any environmental changes are returned as
     part of a new module. This module will then
     support inspection.
     """

    def __init__(self, retain_crashfiles=True):
        """
        :param retain_crashfiles: Does not delete the temporary files upon the raising of exceptions,
            allowing the user to inspect it.
        """
        self.retain = retain_crashfiles
        self.source = []
    def make_boilerplate(self, env: rcb.EnvProxy):
        """

        Makes the boilerplate commentary
        living at the front of each temporary
        file

        :param env: The environment
        :return: A string of commentary
        """


        frame = inspect.currentframe()
        path = frame.f_back.f_back.f_code.co_filename
        path = re.escape(path)

        time = datetime.datetime.now()
        vars = env.as_dict().keys()
        vars = [str(var) for var in vars]
        vars = "\n".join(vars)
        intro = boilerplate_template.format(path=path,
                                    time=time,
                                    environmentals=vars)
        return intro
    def append(self, source: str):
        self.source.append(source)
    def __call__(self, fetch: str, env: rcb.EnvProxy):
        """
        :param fetch: The name of the feature to get out of the source
        :param env: The environment to run the module in.
        :return: Whatever environmental parameter is named fetch.
        """

        #The following lines of code should have a little bit of explanation.
        #
        #We basically create a temporary source file, a temporary
        #environment, and then compile some bytecode while
        #telling python the source is coming from the temporary
        #file.
        #
        #This ensures inspect can track it down.
        #
        #Once this is done, we return the requested environmental variable
        #from the temporary sandbox.

        #Collect sources, and attach the boilerplate code.
        sources = [self.make_boilerplate(env)] + self.source
        sources = "\n".join(sources)
        file = TempCodeFile(sources)

        #Execute. Handle crashes
        #
        #Note that the sandbox maintains some side effects,
        #particularly anything resulting from modifying objects.
        #
        #It really just ensures that the global state is not directly
        #modified.
        partial_sandbox = env.copy()
        code = compile(file.contents, file.path, 'exec')
        try:
            exec(code, partial_sandbox.globals, partial_sandbox.locals)
        except Exception as err:
            if self.retain:
                file.release = False
            raise err

        #Fetch the desired item out of the sandboxed environment.
        return getattr(partial_sandbox, fetch)
