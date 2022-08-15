import ast
import inspect
from typing import Optional

from src import builder

def test():
    try:
        pass
    except:
        pass
    print(6)

source = inspect.getsource(test)
tree = ast.parse(source)
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


reconstruct(tree)

print(stack)

