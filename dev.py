import inspect

from src import rcb
from src import virtual_code

import inspect



builder = virtual_code.CodeBuilder()
code = 'item = 3'
builder.append(code)
code = """\
def hello_world():
\tprint('Hello World')
"""
builder.append(code)
code = "raise Exception('test')"
builder.append(code)

env = rcb.makeEnvFromFrame()
func = builder("hello_world", env)
func()
print(inspect.getsource(func))