import collections
import dataclasses
import textwrap
from typing import List, Tuple, Dict


class FormatUtils:
    """
    A formatter for handling code templates. Notably, will clean
    up the templates, and can handle repeating quantities.

    In addition to the normal formatting of python, this
    adds an additional feature. It is possible to indicate
    that a given formatting keyword or set of keywords
    should accept a list and be joined by a particular string
    before insertion. A format block with a ;!; inside of it is used to
    indicate this condition. For example, given string:

    '{ \n;!; {a} = {b}}

    And give we define
    a = ["a", "b", "c"]
    b = ["1", "2", "3"]

    The formatter will proceed to yield

    'a=1, \n b=2, \n c=3

    Needless to say, the lists must be the same length.
    """


    multifill_break_sequence = ";!;"

    @dataclasses.dataclass
    class format_block:
        regex_replace_target: str
        contents: str
    @staticmethod
    def clean_template(item: str) -> str:
        """Ensures templates which are defined in class are properly deindented"""
        return textwrap.dedent(item)
    @classmethod
    def get_format_blocks(cls, template: str)->List[format_block]:
        """Gets format names out of strings. Respects balancing"""
        #Does a depth based analysis to find balanced top level {} blocks.
        #Todo: Handle edge cases
        depth = 0
        start = 0
        position = 0
        outputs: List[FormatUtils.format_block] = []
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
                target = template[start:position]
                contents = template[start + 1:position - 1]
                block = cls.format_block(target, contents)
                outputs.append(block)
        if depth != 0:
            raise RuntimeError("Lacking close } for some open {")
        return outputs
    @classmethod
    def split_mulifill_block(cls, block: str)->Tuple[str, str]:
        """Splits multifill into the join string and subtemplate."""
        start_index = block.find(cls.multifill_break_sequence)
        end_index = start_index + len(cls.multifill_break_sequence)
        return block[:start_index], block[end_index:]
    @classmethod
    def is_multifill_format_block(cls, block: str):
        return cls.multifill_break_sequence in block
    @classmethod
    def compile_multifill_block(cls, contents: str, kwargs):
        join_string, subtemplate = cls.split_mulifill_block(contents)
        subrequirements = cls.get_format_blocks(subtemplate)

        requirement_names: List[str] = []
        requirement_list_features: List[List[str]] = []
        #Perform sanity checking, and collect zip features
        for subrequirement in subrequirements:
            subcontent = subrequirement.contents
            if subcontent not in kwargs:
                raise KeyError("Multifill keyword %s not found" % subcontent)
            feature = kwargs[subcontent]
            if not isinstance(feature, list):
                raise ValueError("Multifill keyword %s was not a list or tuple" % subcontent)
            requirement_names.append(subcontent)
            requirement_list_features.append(feature)
            if len(requirement_list_features[0]) != len(feature):
                raise ValueError("Multifill keyword %s is of length %s, but should be %s"
                                 % subcontent, len(feature), len(requirement_list_features[0]))
        #Dictionary represents a particular combination of keywords.
        # List iterates over constructed combinations
        format_dictionaries = [{name : substitution for name, substitution
                               in zip(requirement_names, substitution_values)}

                               for substitution_values in zip(*requirement_list_features)
                               ]
        outputs: List[str] = []
        for format_dict in format_dictionaries:
            compiled_template = subtemplate.format(**format_dict)
            outputs.append(compiled_template)
        final_output = join_string.join(outputs)
        return final_output
    def __init__(self, template: str):
        self.template = template
    def __call__(self, **kwargs):
        replacement_targets = {}
        formatting_requirements = self.get_format_blocks(self.template)
        for specific_format_block in formatting_requirements:
            contents = specific_format_block.contents
            target = specific_format_block.regex_replace_target
            if self.is_multifill_format_block(contents):
                replacement_targets[target] = self.compile_multifill_block(contents, kwargs)
            else:
                if contents not in kwargs:
                    raise KeyError("Singlular keyword %s not found in inputs" % contents)
                replacement_targets[target] = kwargs[contents]
        output = self.clean_template(self.template)
        for to_substitute, substitution in replacement_targets.items():
            output = output.replace(to_substitute, substitution)
        return output




class Template(FormatUtils):
    """
    A template consists of a sequence of
    format ready features, all expected to
    go off together. The primary output
    of a template will be the "template" class
    parameter, once it has it's keywords filled in

    It is possible to define additional class attributes,
    however, consisting of things beginning with
    the word template. In this case, these will act
    as aliases for words seen in the primary template,
    and can automatically substitute.

    As in the formatter, it is the case calling is what
    is required to use the class.
    """
    primary_template_name = "primary_template"
    subtemplate_suffix_keyword = "subtemplate"



    @classmethod
    def get_subtemplate(cls, name: str)->str:
        if not hasattr(cls, name):
            raise AttributeError("No subtemlate attribute of name %s detected" % name)
        item = getattr(cls, name)
        if not isinstance(item, str):
            raise AttributeError("Attempt to retrieve subtemplate of name %s which was not string" % name)
        return item
    @classmethod
    def get_primary_template(cls)->str:
        """Get the primary template, handling errors if it is not found."""
        #A primary template matches the class definition of it's attribute name.
        if cls.primary_template_name not in cls.__dict__:
            raise AttributeError("Primary template not detected. No attribute of name %s" % cls.primary_template_name)
        template = getattr(cls, cls.primary_template_name)
        if not isinstance(template, str):
            raise AttributeError("Primary template named %s is not a string" % cls.primary_template_name)
        return template


    def get_keyword_or_compile_subtemplate(self, name: str, kwargs: dict):
        """
        If a subtemplate with the name is found, go compile it.
        Else, fetch the requirement from the keywords
        """


    @classmethod
    def compile_template(self, template: str, kwargs):
        def get_keyword_or_compile_subtemplate(name: str):
            if hasattr(self, name):
                subtemplate = self.get_subtemplate(name)
                return self.compile_template(subtemplate, kwargs)
            return kwargs[name]




        format_blocks = cls.get_format_blocks(template)
        for block in format_blocks:
            contents = block.contents
            if cls.is_multifill_format_block(contents):
                join_string, subtemplate = cls.split_mulifill_block(contents)
            else:

    def __call__(self, **kwargs):
        subtemplates = self.get_user_subtemplates()
        def compile_template(name: str, kwargs: dict):
            if template not

    @classmethod
    def get_template_dependencies(cls, name: str)->:
        """fetch all keywords required by the particular template. """
        template = getattr(cls, name)
        format_blocks = cls.get_format_blocks(template)
        for block in format_blocks:
            contents = block.contents
            if cls.




class Class_Features_Template(Formatter):
    """
    A template for creating class features code blocks
    """
    magic_name = "__Class_Features"
    init_params_template = "{ , ;!; {parent_feature_name} : {parent_feature_type}}"
    init_parent_assignment_template = "{            ;!; self.{parent_feature_name} = {parent_feature_name}\n}"
    init_self_assignment_template = "{"
    method_params_template = "{ , ;!; {method_param_name} : {method_param_type}}"


    primary_template = """\
    
    class {magic_name}_{name}:
        def __init__(self{ , ;!; {parent_feature_name}: {parent_feature_type}}):
{       ;!;{methods}}
    {magic_name}_{name} = {magic_name}_{name}({ ' ;!; {parent_feature_name}})
    """
    methods_template = """\
    def {method_name}({ , ;!; {method_param} : {method_type}}):
        {method_code}
    """

    def __init__(self):
        super().__init__(self.template)
    def __call__(self,
                 name: str,
                 parent_feature_name: List[str],
                 parent_feature_type: List[str],
                 method_name: List[str],
                 method_parameters: List[str],
                 method_code: List[str]):
        format_dict = {}
        format_dict["name"] = name
        format_dict["parent_feature_name"] = parent_feature_name
        format_dict["parent_feature_type"] = parent_feature_type
        format_dict["method_name"] = method_name
        format_dict["method_parameters"] = method_parameters
        format_dict["method_code"] = method_code
        format_dict["magic_name"] = self.magic_name
        return super().__call__(**format_dict)


instance = Class_Features_Template()
instance("a", [], [], [], [], [])