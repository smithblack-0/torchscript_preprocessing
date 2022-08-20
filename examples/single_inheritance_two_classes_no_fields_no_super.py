# Static inheritance analysis. No class methods. No super calls
"""
* Static Function inheritance
* Single inheritance
* Two classes
* No defined fields
"""

### Initial

class base():
    def to_override(self):
        print("boop")
    def to_inherit(self):
        print("boop")
    pass

class Inherits(base):
    def to_override(self):
        print("overridden")
    def new_feature(self):
        print("new")

### Final

class Inherits():
    def to_inherit(self):
        print("boop")
    def to_override(self):
        print("overridden")
    def new_feature(self):
        print("new")