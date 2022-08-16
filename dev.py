import ast
import inspect
import astunparse
from typing import Optional

from src import builder

def test():
    with open("src/builder.py") as f:
        pass
    new = 4
    try:
        pass
    except:
        pass
    print(6)
    del new.node
class base:
    pass

class test(base):
    pass

source = inspect.getsource(test)
tree = ast.parse(source)
for item in ast.walk(tree):
    print(item)
stack = builder.StackSupportNode()
stack = stack.push(tree)
print(dir(stack))


def reconstruct(node: ast.AST, helper: Optional[builder.StackSupportNode]=None):
    if helper is None:
        helper = builder.StackSupportNode()
    context = helper.push(node)
    for fieldname, child in context.get_child_iterator():
        if isinstance(child, ast.AST):
            child = reconstruct(child, context)
        context.place(fieldname, child)
    return context.pop()


test = reconstruct(tree)
test = ast.fix_missing_locations(test)
source = astunparse.unparse(test)
print(source)

