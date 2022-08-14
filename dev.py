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

def reconstruct(node: ast.Module, helper: Optional[builder.StackSupportNode]=None):
    if helper is None:
        helper = builder.StackSupportNode()
    context = helper.push(node)
    for fieldname in context.fields:
        context_attr = getattr(context, fieldname)
        node_attr = getattr(node, fieldname)
        if isinstance(node_attr, list):
            for item in node_attr:
                context_attr.append(reconstruct(item, context))
        else:
            setattr(context, fieldname, reconstruct(node_attr, context))
    return context.pop()


reconstruct(tree)

print(stack)

