from typing import *
import transforms
import astroid
import inspect
import torch

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
trans = [transforms.extract_inline_functions, transforms.walk]
pipeline = transforms.Pipeline(trans)
transforms.walk(tree, tree, pipeline)

print("post")
print(tree.as_string())