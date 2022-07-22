# Introduction

torchscript is pretty amazing. 
One can see speedup's of up to 100x when
using it. Nonetheless, it has it's indisputible flaws.

One of these is the lack of solid support for object
oriented programming. After one too many frusterating
design moments, and a flash of inspiration/madness, I have
decided I wish to modify torchscript to support
said paradynms. 

This is the design thread for this modification. If it is the
opinion of the community I should not go forward with this, I might
instead turn it into a preprocessor.

# Objectives

Overall, the objectives here might be summarized as
enabling the usage of inheritance and class methods/properties
within a torchscript environment. The primary focus is
on inheritance, but while I understand torchscript classes
properly I might as well look into supporting class attributes
 
# Insights

## Class Rewriting for Function inheritance with no super awareness

It is the case that a limited format of inheritence, in
which only methods are inherited and in which superclass is not checked,
is a well defined problem. Consider the situation below:

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
        
       
     
```

inheritor could, with proper method functionality,
be rewritten as a compilable object

```
class inheritor()
    def __init__():
        ... do some setup
        ... do base setup
        ... do more setup
    def function_to_override(self):
        ... do inheritor stuff
    def function_to_inherit(self):
        ... do base stuff
```

Notice all that was required was to transfer the
needed method onto the inheritor class, and transfer
init code from the base into the class. This implies to me
much the same could be done by modifying the ast tree before 
primary compiling. 

I already checked, and the callback system for 
torchscript looks like it can handle this. If not, I will
just add something to '_jit_internal'

What is needed is to, in python, modify 
'jit.recursive._compile_and_register_class' such
that it passes the resolution callback, "rcb", into
"get_jit_class_def". Then, over in "jit.frontend.get_jit_class_def", 
we go ahead and insert code that recursively gebnerates the
ast entries under the base key, and then attach inherited
functions into the ast tree of the base class. It
then has access to these functions.

A little bit hacky, but it should work. But there is more that can be
done. 

TL;DR

* Modify the python ast parsor to fetch and incorporate overrides before parsing the class

## Function inheritance with full support

The builtin functions and methods of python that utilize and 
work with inheritance are, as far as I know:

* super()
* isinstance()
* issubclass()
* object.mro()

(Please tell me if I missed anything)

These will not properly work with the above modifications. However, I believe they too
are recoverable with minimal c++ work. This will, however,
require more significant modifications.

