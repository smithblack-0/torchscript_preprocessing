import collections
import dataclasses
import textwrap
from typing import List, Tuple


class Formatter:
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
    @dataclasses.dataclass
    class format_block:
        regex_replace_target: str
        contents: str

    multifill_break_sequence = ";!;"
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
        outputs: List[Formatter.format_block] = []
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
    def split_mulifill_block(self, block: str)->Tuple[str, str]:
        start_index = block.find(self.multifill_break_sequence)
        end_index = start_index + len(self.multifill_break_sequence)
        return block[:start_index], block[end_index:]
    @classmethod
    def is_multifill_format_block(cls, block: str):
        return cls.multifill_break_sequence in block
    def compile_multifill_block(self, contents: str, kwargs):
        join_string, subtemplate = self.split_mulifill_block(contents)
        subrequirements = self.get_format_blocks(subtemplate)

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

class Class_Features_Template(Formatter):
    """
    A template for creating class features code blocks
    """
    magic_name = "__Class_Features"
    init_params_template = "{ , ;!; {parent_feature_name} : {parent_feature_type}}"
    init_parent_assignment_template = "{            ;!; self.{parent_feature_name} = {parent_feature_name}\n}"
    init_self_assignment_template = "{"
    method_params_template = "{ , ;!; {method_param_name} : {method_param_type}}"


    class_feautres_template = """\
    
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