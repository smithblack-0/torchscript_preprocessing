import astroid
import inspect
from src.StringExec import StringScriptContext


def gentest():
    for i in range(10):
        y = yield 3
        yield i

gen = gentest()
print(next(gen))
print(next(gen))