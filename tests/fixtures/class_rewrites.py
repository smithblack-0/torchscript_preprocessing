"""
This is a collection of intial python files
and final rewritten files to keep myself oriented.

Objectives:

Build cases for:

* Single, Multiple, Chained inheritance
* No, instance fields, class fields,
* No, instance super calls, class super calls.
* No, parent instance, parent class field access.
* No, instance functions inherited, class function inherited

"""

import enum

class Inheritance(enum.Enum):
    none: str = "none"
    single: str = "single"
    chained: str = "chained"
    multiple: str = "multiple"

class Example():
    """
    The base example. Should be revised by subclass examples
    """