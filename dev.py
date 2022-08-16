import astroid
import inspect
from src.StringExec import StringScriptContext


def scope():
    item = 4
    item

node = astroid.parse(inspect.getsource(scope))
print(node)
