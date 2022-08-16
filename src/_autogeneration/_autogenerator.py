"""

Responsible for autogeneration to save me time

"""

import ast
import _ast
from typing import List
from typing import get_args
from _ast_grammer import grammer_tree
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
    This is a autogenerated node to support the 
    creation of ast nodes of variety
    {ClassName}
    \"\"\"
    fields = ({field_info})
    annotations = ({annotation_info})
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




setup_template = "self.{name}: Optional[{typing}] = None"
list_setup_template = "self.{name}: {typing} = []"
usage_template = "self.{name},"
fieldinfo_template = "\"{name}\", "
annotationsinfo_template = "{annotation}, "

#Go generate required typing info

outcome = grammer_tree.lookup(_ast.Suite.__name__)

codeblocks: List[str] = []
for node_data in grammer_tree.iter():
    print("making code for", node_data.name)
    ast_typing = "ast." + node_data.ast_typing.__name__
    fields_data = []
    annotations_data = []
    fields_setup = []
    fields_loading = []


    if node_data.arguments is not None:
        for sig in node_data.arguments:
            fields_data.append(fieldinfo_template.format(name=sig.name))
            annotations_data.append(annotationsinfo_template.format(annotation=sig.type_str))
            fields_loading.append(usage_template.format(name=sig.name))
            if sig.list:
                fields_setup.append(list_setup_template.format(name=sig.name, typing=sig.type_str))
            else:
                fields_setup.append(setup_template.format(name=sig.name, typing=sig.type_str))

    fields_data = "".join(fields_data)
    annotations_data = "".join(annotations_data)
    feature_setup = "\n        ".join(fields_setup)
    field_loading =  "\n            ".join(fields_loading)

    # Format the class, and append
    classcode = class_build_template.format(
        ClassName=node_data.name,
        astType=ast_typing,
        feature_storage=feature_setup,
        feature_load=field_loading,
        field_info=fields_data,
        annotation_info=annotations_data
    )
    codeblocks.append(classcode)




#Make and store builder source
source = stub_source + "".join(codeblocks)
with open(destination, mode="w") as f:
    f.write(source)
