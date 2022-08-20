"""
Analyzes static inheritance with fields
* Simple, 2 part inheritance.
* Static function analysis and rewriting
* Inherited fields, per instance, must be included
* super calls.
"""

### Initial ###


class base():
    def to_override(self):
        print("boop")
    def to_inherit(self):
        print(self.doop)
    def __init__(self, doop):
        self.doop = doop

#Compile target:
class inherits(base):
    def to_override(self):
        print("overridden")
    def __init__(self):
        super().__init__(5)

### Final ###

class inherits2():
    def to_override(self):
        print("overridden")
    def to_inherit(self):
        print(self.doop)
    def __init__(self):
        self.__base_init(5)
    def __base_init(self, doop):
        self.doop = doop
