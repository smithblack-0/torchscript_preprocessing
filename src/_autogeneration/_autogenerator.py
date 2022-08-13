"""

Responsible for autogeneration to save me time

"""

import ast
from typing import List

import _ast_grammer
import inspect

### Builder autogeneration
#
#This fetches all known nodes from ast,
#then goes and creates a builder for each one.

stub_source = open("_builder_stub.py").read()
nodes = [value for key, value in vars(ast).items()
         if inspect.isclass(value) and value is not ast.AST and issubclass(value, ast.AST)]
destination = "../builder.py"


#Create the templates
class_build_template = """
class {ClassName}BuilderNode(StackSupportNode, typing={astType}):
    \"\"\"
    This is a node to support the 
    creation of ast nodes of variety
    {ClassName}
    \"\"\"
    @property
    def node(self)->{astType}:
        return self._node
    def __init__(self, node: {astType}, parent: Optional[StackSupportNode]=None):
        super().__init__(node, parent)
        {feature_storage}
    def construct(self)->{astType}:
        return {astType}(
            {feature_load}
        )
"""
storage_template = "self.{name}: {typing} = node.{name}"
usage_template = "self.{name},"

#Go generate required typing info

_ast_grammer.get_signature_variety(ast.BoolOp.__name__)
codeblocks: List[str] = []
for node in nodes:
    #Get the info
    name = node.__name__
    type = "ast." + name
    signature = _ast_grammer.get_signature_variety(name)

    if signature is not None:
        #Create the feature storage and usage code
        feature_storage = [storage_template.format(name=sig.name, typing = sig.typing) for sig in signature]
        usage = [usage_template.format(name=sig.name) for sig in signature]

        feature_storage = "\n        ".join(feature_storage)
        usage = "\n            ".join(usage)

        #Format the class, and append
        classcode = class_build_template.format(
            ClassName=name,
            astType=type,
            feature_storage=feature_storage,
            feature_load=usage
        )
        codeblocks.append(classcode)

#Make and store builder source
source = stub_source + "".join(codeblocks)
with open(destination, mode="w") as f:
    f.write(source)
