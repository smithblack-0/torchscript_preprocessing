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
from typing import List, Tuple, Set, Union, Any, Generator

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


"""

{       , self.{name} = {value} \n}
"""


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
    subtemplates: Dict[str, str] = {} #Any number of additional templates with associated aliases. May also reference each other
    @dataclasses.dataclass
    class CompileStub:
        """
        A stub generated during initialization.
        Indicates what needs to be filled in for the template to work.
        """
        template: str
        alias_dependencies: List[str] = dataclasses.field(default_factory = lambda : [])
        direct_dependencies: List[str] = dataclasses.field(default_factory = lambda : [])
        list_dependencies: List[Tuple[str, str]] = dataclasses.field(default_factory= lambda : [])
    @dataclasses.dataclass
    class dependencyStub:
        name: str
        join_str: str = ""
        is_alias: bool = False
        is_direct: bool = False
        is_list: bool = False
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
    def is_predefined_attribute(self, attribute_name: str):
        """
        Checks if the given attribute is defined at the class level,
        which indicates it is the same in all instances.
        """
        instance_class = self.__class__
        return hasattr(instance_class, attribute_name)
    def create_dependency_attribute(self, dependency: str)->Generator["Template.dependencyStub", None, None]:
        """Register template exists on the class. Indicates dependency type."""
        if dependency in self.subtemplates:
            #This is an alias to another subtemplate. Create no attribute
            yield self.dependencyStub(name=dependency, is_alias=True)
        elif ',' in dependency:
            #This is a list dependency. Create a list for each subdependency.
            subtemplate, join_string = dependency.split(",")
            subdependencies = self.get_format_names(subtemplate)
            for subdependency in subdependencies:
                if not self.is_predefined_attribute(subdependency):
                    if hasattr(self, dependency):
                        raise AttributeError("Attempt to create dependency of name %s twice")

                    assert not hasattr(self, dependency)
                    setattr(self, dependency, [])
                yield self.dependencyStub(name=subdependency, join_str=join_string, is_list=True)
        else:
            #This is a direct set dependency. Create a b
            if not self.is_predefined_attribute(dependency):
                assert not hasattr(self, dependency)
                setattr(self, dependency, None)
            yield self.dependencyStub(name=dependency, is_direct=True)

    def __init__(self):
        """
        :param string: A string with format blocks, indicated by {format}
        """
        #Figure out the dependencies required. Dependencies will consist of
        # aliases, direct replacement dependency, or list join dependencies.
        # They are either atttributes the user must fill in, or a subtemplate
        # that must compile first.
        #
        # For each template, we turn this into a compile stub, create instance
        # attribute for user interaction, and store away the compile stub for
        # later usage. The class promises that if the user attributes are configured
        # correctly, the alias will compile correctly.

        templates = self.subtemplates.copy()
        if self.template_name in templates:
            raise RuntimeError("Cannot have a subtemplated names %s while also having a primary template named %s" % self.template_name)
        templates[self.template_name] = self.template
        dependencies: Dict[str, Template.CompileStub] = {}
        for name, template in templates.items():
            direct_dependencies = []
            list_dependencies = []
            subtemplate_dependencies = []
            template_specific_dependencies = self.get_format_names(template)
            for specific_dependency in template_specific_dependencies:
                registration_stub_gen = self.create_dependency_attribute(specific_dependency)
                for stub in registration_stub_gen:
                    if stub.is_direct:
                        direct_dependencies.append(stub.name)
                    elif stub.is_alias:
                        subtemplate_dependencies.append(stub.name)
                    elif stub.is_list:
                        list_dependencies.append((stub.name, stub.join_str))
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
        # Catches and raises if it gets stuck. Not particularly efficient, but does it really need to be
        # so?

        compiled_subtemplates = {}
        compilation_targets = self.compile_info.copy()
        while True:
            progressing = False
            for name in compilation_targets:
                if self.dependencies_satisfied(compilation_targets[name]):
                    progressing = True
                    stub = compilation_targets.pop(name)
                    dependencies = self.get_dependencies(stub, compiled_subtemplates)
                    if name == self.template_name:
                        return stub.template.format(**dependencies)
                    else:
                        compiled_subtemplates[name] = stub.template.format(**dependencies)
                    break
            if not progressing:
                raise RuntimeError("Recursive or invalid template")

class dev_template(Template):
    template = """
    {{item1} = {item2},     \n}
    {replace}
    """


instance = dev_template()
instance()
