"""
Purpose:

Pseudotemporary file. Should be refactored later.

Explore how to handle class attributes and inheritance in a naive situation.

* Classes live at the top (module) level.
* Any classes which are defined will be placed into the top level of the program and will be
 available perpetually into the future.


Code production design philosophy is:

* A class in python is composed of, from a compiler level,
 essentially three parts. These are the environment, the class attributes, and the instance attributes
* We break up classes into these three fundamental parts.
    * There is a class_features part
    * There is an instance_features part
    * There is an environmental_wrapper part

The environmental wrapper is declared on site, whereas the instance and class features are declared elsewhere.

Torchscript will compile this.
"""
from typing import List, Tuple, Set, Union, Any

import torch
import re
import textwrap
import enum
import dataclasses
from src import StringExec
from typing import Dict

#Define magic names and such

wrapper_magic_name = "__environmental_wrapper"
class_feature_magic_name = "__class_level_features"
instance_feature_magic_name = "__instance_level_features"

class Template():
    """
    Runtime class designed to generate a template
    builder, capable of building a template part
    by part as the information becomes available.

    One may assign attributes of the template with
    particular values.
    *   The class attributes "template" and "template_name" determine, respectively, what the overall template
        is and what it is called internally. template_name will only have to be changed on getting an error of a
        collision
    *   Simple subtemplates are a single simple value. They are detected by regex when you set up a format
        bracket, for example: 'self.{var_name} = {var_assignment}'. They create an attribute of the same name filled
        with None on the class, and which must be set before proceeding.
    *   List subtemplates are indicated with a format bracket, and two items with parenthesis inside. The first
        item in parenthesis is the template itself. The second is the join directive. Each variable detected
        as a dependency will generate an attribute, in which a list of the same length can be placed. These
        will then be evaluated in sequence, and joined together. For example,

        {self.{var_name} = {var_frame_name},  HfooH }
        var_name = ["a", "b"]
        var_frame_name = ["f", "u"]

        would become:

        self.a = f HfooH self.b = u
    """

    template: str = "" # The primary template, and what will be returned
    template_name: str = "primary"
    subtemplates: Dict[str, str] = [] #Any number of additional templates with associated aliases. May also reference each other
    dependency_pattern = re.compile(r"{(.*?)}")


    @dataclasses.dataclass
    class CompileStub:
        template: str
        alias_dependencies: List[str]
        direct_dependencies: List[str]
        list_dependencies: List[Tuple[str, str]]
    @staticmethod
    def clean_template(item: str)->str:
        return textwrap.dedent(item)
    @staticmethod
    def get_format_names(template: str)->List[str]:
        """Gets format names out of strings. Respects balancing"""
        #Does a depth based analysis to find balanced top level {} blocks.
        #Todo: Handle edge cases
        depth = 0
        start = 0
        position = 0
        outputs: List[str] = []
        while True:
            next_open_index = template.find("{", position)
            next_close_index = template.find("}", position)
            if next_close_index == -1:
                # Done with iteration
                break
            position = next_open_index if next_open_index < next_close_index \
                                          and next_open_index != -1 else next_close_index
            if position == next_open_index:
                if depth == 0:
                    start = position
                depth += 1
            else:
                depth -= 1

            position += 1
            if depth == 0:
                stringslice = template[start + 1:position - 1]
                outputs.append(stringslice)
        return outputs
    def __init__(self):
        """
        :param string: A string with format blocks, indicated by {format}
        """

        #Figure out the dependencies required. Dependencies will consist of
        # aliases, direct replacement dependency, or list join dependencies.
        #
        # For each template, we turn this into a compile stub, create instance
        # attribute for user interaction, and store away the compile stub for
        # later usage.

        templates = self.subtemplates.copy()
        if self.template_name in templates:
            raise RuntimeError("Cannot have a subtemplated names %s while also having a primary template named %s" % self.template_name)
        templates[self.template_name] = self.template
        template_names = templates.keys()
        dependencies: Dict[str, Template.CompileStub] = {}
        for name, template in templates.items():
            direct_dependencies = []
            list_dependencies = []
            subtemplate_dependencies = []
            template_specific_dependencies = self.get_format_names(template)
            for specific_dependency in template_specific_dependencies:
                if specific_dependency in template_names:
                    #This is an alias. Do nothing
                    subtemplate_dependencies.append(name)
                elif "," in specific_dependency:
                    #This is a list subtemplate. Go set it up
                    subtemplate, join_string = specific_dependency.split(",")
                    subdependencies = self.get_format_names(subtemplate)
                    for subdependency in subdependencies:
                        assert not hasattr(self, subdependency)
                        setattr(self, subdependency, [])
                    list_dependencies.append((join_string, subdependencies))
                else:
                    #Standard attribute. Setup
                    assert not hasattr(self, specific_dependency)
                    setattr(self, specific_dependency, None)
                    direct_dependencies.append(specific_dependency)
            stub = self.CompileStub(template,subtemplate_dependencies, direct_dependencies, list_dependencies)
            dependencies[name] = stub
        self.compile_info = dependencies
    def dependencies_satisfied(self, dependencies: "Template.CompileStub", compiled_names: List[str])->bool:
        """Checks if all the listed dependencies are either attributes or in compiled name"""
        for dependency in dependencies:
            if dependency in compiled_names:
                continue
            if hasattr(self, dependency):
                if getattr(self, dependency) is None:
                    raise AttributeError("Attribute of name %s never set on template" % dependency)
                continue
            return False
        return True
    def get_dependencies(self, dependencies: Set[str], compiled_subtemplates: Dict[str, str])->Dict[str, str]:
        """Gets the dependencies, out of either the compiled subtemplate or the class attributes"""
        output_dictionary = {}
        for dependency in dependencies:
            if dependency in compiled_subtemplates:
                output_dictionary[dependency] = compiled_subtemplates[dependency]
            else:
                output_dictionary[dependency] = getattr(self, dependency)
        return output_dictionary
    def __call__(self)->str:
        """Yields a compiled template"""
        # A quick and dirty template compiler capable of ensuring that the template is filled
        # properly. Goes through list of templates and required_dependencies, and tracks down, then executes,
        # anything which is compilable but has not been compiled. aliases are filled in as we go.
        # Catches and raises if it gets stuck. Not particularly efficient, but we are not going to
        # spent much time here.

        compiled_subtemplates = {}
        compilation_targets = self.compile_info.copy()
        while True:
            progressing = False
            for name in compilation_targets:
                if self.dependencies_satisfied(compilation_targets[name]):
                    progressing = True
                    stub = compilation_targets.pop(name)
                    dependencies = self.get_dependencies(stub, compiled_subtemplates)
                    if name is self.template_name:
                        return stub.template.format(**dependencies)
                    else:
                        compiled_subtemplates[name] = stub.template.format(**dependencies)
                    break
            if not progressing:
                raise RuntimeError("Recursive or invalid template")



class class_features_template():
    """
    A template for creating a class representing class features
    """
    class_feature_magic_name = "__class_features"
    subtemplate

    template = """\
    class {class_feature_magic_name}_{class_name}:
        def __init__(self, {parent_class_feature}):
            {(parent_class_feature_assignments), (     \n)} 
    
    
    """
