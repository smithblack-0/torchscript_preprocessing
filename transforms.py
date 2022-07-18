"""

Transforms perform needed modifications within
the broader context of the model. They
are capable of performing a variety of neat tricks.

They operate per module, and are fed the module pipeline,
the top level tree, and the current node.

"""
import ast
import builtins
import copy

import astroid
import astor
from typing import Callable, List, Tuple


class Pipeline():
    """

    A pipeline applies a sequence of transforms to a node, then
    returns the result.

    """

    def __init__(self, transforms: List[Callable]):
        self.transforms = transforms
    def __call__(self,
                 node: astroid.NodeNG,
                 root: astroid.Module,
                 **kwargs) -> astroid.NodeNG:
        for transform in self.transforms:
            transform(node, root, self, **kwargs)
        return node


def extract_inline_functions(
        node: astroid.NodeNG,
        root: astroid.Module,
        pipeline: Pipeline,
        **kwargs
    ) -> Tuple[astroid.NodeNG, astroid.NodeNG]:
    """

    This transform will detect when
    an inline function is present, and
    will start an extraction session.

    Once the session is done, the new class will
    be inserted into the root, right before the
    current class, and the node replaced with a
    call to a proxy class.

    If no such function is detected, we simply
    go ahead and return the node


    :param node: The current node
    :param root: The root node
    :param pipeline: The pipeline for node processing
    :return: A astroid Node
    """
    if not isinstance(node, astroid.FunctionDef):
        ## Ignore anything not a function def
        return node
    if isinstance(node.parent, (astroid.ClassDef, astroid.Module)):
        ## Ignore if the parent is a class or a module
        return node
    ## Enter editing mode. Begin by defining a virtual root

    node = node
    virtual_root = node.root()

    ## Define the feature templates

    class_template = """ 
class {name}():
\tdef __init__(self, 
\t\t\t{init_parameters}
\t\t\t):
\t\tpass
\t\t{init_code}
\tdef __call__(self, 
\t\t\t{call_args}):
\t\t{call_load}
        
        #Original function code begins

\t\t{call_source}
    """
    call_args_template = "{name}, \n\t\t\t"
    init_parameters_template = "{name} : {type}, \n\t\t\t"
    init_code_template = "self.{name} = {name} \n\t\t"
    call_load_template = "{name} = self.{name} \n\t\t"
    call_source_template = "{name} \n\t\t"
    function_source_template = "{name} \n\t\t"

    ## Extract the required environmental calls, then generate
    #all related code

    def extract_environmental_args(node, root):
        output = []
        lambda_count = 0
        children = node.get_children()
        for child in children:
            if isinstance(child, astroid.Lambda):
                continue
            if isinstance(child, astroid.Name):
                source = child.inferred()
                assert len(source) == 1
                source = source[0]
                if not root.parent_of(source):
                    if source.is_lambda:
                        name = "lambda_" + str(lambda_count)
                        lambda_count += 1
                        output.append((name, 'Callable'))
                    if source.is_function:
                        output.append((child.name, 'Callable'))
                    if isinstance(source, astroid.Const):
                        output.append((child.name, source.pytype()))
            if not isinstance(child, astroid.Arguments):
                output = output + extract_environmental_args(child, root)
        return output

    #Construct init parameter, load, and save code snippets.
    environmental = extract_environmental_args(node, node)


    init_code = ""
    init_parameters = ""
    call_load = ""
    for item in environmental:
        name, typing = item
        init_parameters = init_parameters + init_parameters_template.format(name=name, type=typing)
        init_code = init_code + init_code_template.format(name=name)
        call_load = call_load + call_load_template.format(name=name)

    #Construct the call arguments
    call_args = node.args.format_args()
    if len(call_args) > 0:
        call_args = call_args.split(",")
        call_args = [call_args_template.format(name=item) for item in call_args]
        call_args = "".join(call_args)

    #Construct the function internals source. Do this
    #by transfering these parts of the tree onto a
    #virtual module, then turning it back into source

    source_extractor = astroid.Module("extractor")
    transplant = node.body
    while len(transplant) > 0:
        item = transplant.pop(0)
        item.parent = source_extractor
    source_extractor.body = transplant
    call_source = source_extractor.as_string()
    call_source = call_source.split('\n')
    call_source = [call_source_template.format(name=item) for item in call_source]
    call_source = "".join(call_source)

    #Tidy up the name, then create the source class.

    name = node.qname()
    name = name.replace(".", "_")

    #Create the class source tree, and then insert it into the tree.

    class_source = class_template.format(name=name,
                                         init_parameters=init_parameters,
                                         init_code=init_code,
                                         call_args=call_args,
                                         call_load=call_load,
                                         call_source=call_source)

    #create the virtual root and proxy node. The virtual
    #root will accumulated results, while the proxy node
    #will be run through the pipeline.

    proxy_tree = astroid.parse(class_source).body[0]
    proxy_tree.parent = virtual_root
    ancesters = list(node.node_ancestors())
    ancester = ancesters[-2]
    insert_point = [i for i, item in enumerate(node.root().body) if item is ancester]
    insert_point = insert_point[0]
    virtual_root.body.insert(insert_point, proxy_tree)

    ## Modify the tree to incorporate the indirection

    indirection = "{var_name} = {class_name}({environment_passthroughs}) "
    passthroughs = ""
    passthrough_template = "{name}, "
    for item in environmental:
        name, type = item
        passthroughs = passthroughs + passthrough_template.format(name=name)
    indirection = indirection.format(var_name=node.name,
                                     class_name=name,
                                     environment_passthroughs=passthroughs)

    indirection = astroid.parse(indirection)
    indirection = indirection.body[0]
    indirection.parent = node.parent
    insert_point = [i for i, item in enumerate(node.parent.body) if item is node][0]
    node.parent.body[insert_point] = indirection

    ## Run everything from here with the new virtual root.

    _, virtual_root = pipeline(proxy_tree, virtual_root)
    return indirection, virtual_root

def walk(node: astroid.NodeNG, root: astroid.Module, pipeline : Pipeline, **kwargs):
    """

    Continues walking when we are certain there is nothing
    else to be worried about.

    :param node:
    :param root:
    :param pipeline:
    :param kwargs:
    :return:
    """
    def get_next_sibling(node: astroid.NodeNG):
        parent = node.parent
        if parent is None:
            return None
        breakflag = False
        for item in parent.get_children():
            if breakflag is True:
                return item
            if item is node:
                breakflag = True
        return None

    child = next(node.get_children())
    while child is not None:
        child, root = pipeline(child, root)
        child = get_next_sibling(child)


