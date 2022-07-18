
import builtins
from typing import Callable


class _funct_test_internal():
    def __init__(self,
                 outer: builtins.int,
                 item3: builtins.int,

                 ):
        self.outer = outer
        self.item3 = item3

    def __call__(self,
                 extra: Callable,
                 derp,
                 thing: int = 5,
                 *args,
                 **kwargs,
                 ):
        outer = self.outer
        item3 = self.item3

        # Original function code begins

        if False:
            return 34
        item: int = 3
        return item, outer, item3