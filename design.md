
## Inheritance rewriting

Objects depending on inheritance are:

* super()
* isinstance()
* issubclass()
* object.mro()


Basically, we can get away with just rewriting
inheritance in terms of function calls and then modifiy
the _rcb torch works with. This: 


```

class base():
     def __init__(self):
        ...do setup here
     def function_to_inherit(self):
        ... do base stuff
     def function_to_override(self):
        ... do base stuff
        
class inheritor(base)
    def __init__(self):
        ... do some setup
        super().__init__()
        ... do more setup
    def function_to_override(self):
        ... do inheritor stuff
        return super().function_to_override(stuff)

```

Becomes something looking sort of like this

```
__base___init__(self):
    ... do setup here
    
__base_function_to_override(self, stuff)
    ... do stuff here

class inheritor()
    def __init__():
        ... do some setup
        base_init(self)
        ... do more setup
    def function_to_override(self):
        ... do inheritor stuff
        return super()).
    def function_to_inherit(self):
        ... do base stuff
```

And we then compile inheritor from this point forward
## Inline rewriting

So long as you can track down the typing properly,
there should be no problem with inline function
definition and rewriting

Partial, in other words, is relatively practical.


nce are, as far as I know:


(Please tell me if I missed anything)

These will not properly work with the above modifications. However, I believe they too
are recoverable with minimal c++ work. This will, however,
require more significant modifications.

