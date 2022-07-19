import astroid
from utilities import Transform
from utilities import Processor

class Inline_Function(Transform):
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
    """

    #Define class template. This will be filled in to make a proxy
    class_template = """ 
class PROXY_{name}():
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

    #Define the templates for putting together bits of code.
    call_args_template = "{name}, \n\t\t\t"
    init_parameters_template = "{name} : {type}, \n\t\t\t"
    init_code_template = "self.{name} = {name} \n\t\t"
    call_load_template = "{name} = self.{name} \n\t\t"
    call_source_template = "{name} \n\t\t"
    function_source_template = "{name} \n\t\t"

    #Define the environment extractor.
    @classmethod
    def extract_environmental_args(cls, node, root):
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
                output = output + cls.extract_environmental_args(child, root)
        return output

    def __init__(self):
        super().__init__()
    def __call__(self, node: astroid.NodeNG, processor: Processor) -> astroid.NodeNG:
        if not isinstance(node, astroid.FunctionDef):
            ## Ignore anything not a function def
            return node
        if isinstance(node.parent, (astroid.ClassDef, astroid.Module)):
            ## Ignore if the parent is a class or a module. No need to extract.
            return node

        #Go fetch the environmental variables.
        environmental = self.extract_environmental_args(node, node)

        # Construct init parameter, load, and save code snippets.

        init_code = ""
        init_parameters = ""
        call_load = ""
        for item in environmental:
            name, typing = item
            init_parameters = init_parameters + self.init_parameters_template.format(name=name, type=typing)
            init_code = init_code + self.init_code_template.format(name=name)
            call_load = call_load + self.call_load_template.format(name=name)

         # Construct the call arguments
        call_args = node.args.format_args()
        if len(call_args) > 0:
            call_args = call_args.split(",")
            call_args = [self.call_args_template.format(name=item) for item in call_args]
            call_args = "".join(call_args)

        # Construct the function internals source. Do this
        # by transfering these parts of the tree onto a
        # virtual module, then turning it back into source

        source_extractor = astroid.Module("extractor")
        transplant = node.body
        while len(transplant) > 0:
            item = transplant.pop(0)
            item.parent = source_extractor
            source_extractor.body.append(item)
        call_source = source_extractor.as_string()
        call_source = call_source.split('\n')
        call_source = [self.call_source_template.format(name=item) for item in call_source]
        call_source = "".join(call_source)

        # Tidy up the name, then create the source class.

        name = node.qname()
        name = name.replace(".", "_")

        # Create the class source tree, and then insert it into the tree.

        class_source = self.class_template.format(name=name,
                                             init_parameters=init_parameters,
                                             init_code=init_code,
                                             call_args=call_args,
                                             call_load=call_load,
                                             call_source=call_source)
        class_tree = astroid.parse(class_source)
        class_tree = class_tree.body[0]

        #Insert the new class into the tree, then apply indirection

        ancestor = processor.get_ancestor_from_top(node, 1)
        _, front_node = processor.insert_sibling_in_front(ancestor, [class_tree], 0)
        return processor(front_node)
