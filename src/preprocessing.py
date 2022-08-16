"""
The preprocessing algorithm will attempt to resolve

"""

import ast
import astunparse
import builder
import inspect
import StringExec
from typing import List, Dict, Optional, Type, Tuple, Callable, Generator



def preprocess(obj: object):
    """
    Opens a preprocessing case
    centered around the indicated object.
    """
    #Create the node target
    source = inspect.getsource(obj)
    tree = ast.parse(source)
    target = astunparse.unparse(builder.rebuild(tree, lambda stacknode, node : stacknode))

    #Create the module source
    filename = inspect.getsourcefile(obj)
    sourcelines, file_lineno = inspect.getsourcelines(obj)
    source = "\n".join(sourcelines)
    module_tree = ast.parse(source, filename)

    #Get the node located on the source with it's context.
    def predicate(context: builder.StackSupportNode, node: ast.AST):
        """ A predicate for a walk."""
        try:
            return astunparse.unparse(node) == target
        except AttributeError:
            #The unparser will not unparse some features,
            #due to it not making sense.

            #this returns false in these cases
            return False

    definitions = list(builder.capture(module_tree, predicate))
    assert len(definitions) == 1, "Multiple definitions are not allowed"
    context, node = definitions[0]



def test():
    print(4)

preprocess(test)



