import astroid
import inspect
from src.StringExec import StringScriptContext

items = [1, 2, 3]
for item in items:
    items.pop(0)

    print(item)
