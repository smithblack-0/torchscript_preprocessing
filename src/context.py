"""
The preprocessing process requires the creation
of temporary objects which can be checked
by inspect. This is handled by the codeBuilder
package

Objectives:

Create temporary files with boilerplate and debug information
Ensure these temporary files are accessable by inspect.
Ensure these temporary files are capable of producing sane debug information
"""

import io
import os
import pathlib
import tempfile
from typing import List, Callable, Any, Optional


from src import errors
from src import rcb
from src import datastructures
from src import templates




class Context():
    """
    A class to execute code in.

    Opening the context manager will return the
    source code from the underlying code blocks.

    Errors may be caught, and redirected, if the
    error producer is a torch entity.
    """
    def get(self, name: str)->Any:
        """ Attempts to retrieve environmental info"""
        return getattr(self.env, name)
    def __init__(self,
                 root_block: datastructures.CodeBlock,
                 env: rcb.EnvProxy,
                 path: str):
        """
        :param root_block: The root codeblock
        :param env: The environment we are building in
        :param path: The path everything is from.
        """

        #Make root codeblock
        root_src = templates.make_boilerplate_source(path, env)
        msg = "Error occurred within boilerplate text. Please raise a ticket"
        boilerplate_exception = errors.UnhandledPreprocessingError.precompile(msg)

        #Store root and environment
        self.root = datastructures.CodeBlock(root_src, boilerplate_exception, root_block)
        self.env = env.copy()
        self.rcb = rcb.createCallbackfromEnv(self.env)
        self.temp_handle: Optional[io.TextIOWrapper] = None

    def __enter__(self)->datastructures.CompileStub:
        source = self.root.read()
        self.temp_handle = tempfile.NamedTemporaryFile(mode="w",
                                            suffix='.py',
                                            delete=False)

        self.temp_handle.write(source)
        path = self.temp_handle.name
        name = pathlib.Path(path).name
        return datastructures.CompileStub(path, name, source, self.rcb)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_tb is not None:
            #Exception has occurred. Handle exception.
            if isinstance(exc_val, errors.FrontendError):
                exception = self.root.fetch_exception(exc_tb, exc_val.source_range)
            else:
                msg = "Noncontext exception has occurred. Please raise ticket"
                exception = errors.UnhandledPreprocessingError(exc_tb, msg)
            raise exception from exc_val
        else:
            #No exception. Compilation
            #should be done. Clean up file.
            path = self.temp_handle.name
            self.temp_handle.close()
            self.temp_handle = None
            os.remove(path)
