from typing import *
import transforms
import astroid
import inspect
import torch
from transforms import utilities, inline_function

print("here")


def funct():
    outer = 4
    item3 = 6
    def test_internal(extra: Callable, derp,
                      thing: int = 5, *args,  **kwargs):
        if False:
            return 34
        item: int = 3
        lambda_func = lambda x: x
        def test_deeper_internals(a: torch.tensor):
            return 3
            def even_deeper():
                pass
        return item, outer, item3
    return test_internal




code = inspect.getsource(funct)
tree = astroid.parse(code)
print("prior")
print(tree.as_string())
trans =  [transforms.inline_function.Inline_Function()]
processor = utilities.Processor(trans)
new_tree = processor(tree)
print("post")
print(new_tree[0].root().as_string())