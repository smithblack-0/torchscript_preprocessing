import inspect
import ast


def test():
    item = 3 + 3
    item: int = 3

source = inspect.getsource(test)
tree = ast.parse(source)
print(tree)