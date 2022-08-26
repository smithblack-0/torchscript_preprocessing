import collections
import dataclasses
import textwrap
from typing import List, Tuple, Dict, Union




class SubtemplateCompileFailure(Exception):
    def __init__(self,template_name: str, template: str, name: str):
        #analyze the failure point to identify where to put the feedback information
        #
        #We break the template apart by line numbers, and isolate the lines
        #with the error occurring. We then go intersperse * characters
        #under wherever the erroring region is occuring.
        message = "\nAn error occurred while compiling template %s looking at name '%s'\n" % (template_name, name)
        message += "Template: \n"
        message += template
        self.name = template_name
        self.template = template
        super().__init__(message)


class TemplateKeyNotFound(Exception):
    def __init__(self, name: str):
        self.name = name
        message = "\ntemplate or keyword of name '%s' was not found" %name
        super().__init__(message)

class Template():
    """
    A template consists of a sequence of
    format ready features, all expected to
    go off together. The primary output
    of a template will be the "template" class
    parameter, once it has it's keywords filled in

    --- Formatting and keywords ---

    Formatting is performed much as in standard python,
    with format blocks indicated by {}. Only keywords are allowed,
    and they may be passed when beginning a format.


    -- deAliasing --

    It is possible to reference a template with another template. This is known as
    deAliasing. This will cause the dependent templates to be compiled first, and
    fed into the calling template. For example, given the sequence of template attributes

    the_name = "Frank"
    what_he_says = "Hello, my name is {the_name}"
    what_I_say = "Then he said '{what_he_says}'"

    Formatting 'what_I_say' will yields:

    "Then he said 'Hello, my name is Frank'"

    --- Multifill formatting ---

    One very useful ability to possess when putting together code is some
    sort of formatting instruction to leverage python string join. That is,
    something which can accept a list, or sequence of lists, and join them
    together after applying a template.

    This is multifill formatting.

    Multifill formatting is performed by opening a format block and placing inside it
    two string sections, consisting of the join string and the multifill template. The
    two sections should be separated by the multifill_break_string, which by default
    is ';!;'. An example would be:

    { OMG!!! \n;!; {Person}, whose mentor is {Mentor}, has graduated in {year}}

    This can then be fed either a list of strings or a straightforward string for the
    formatting keywords. Multiple lists can be fed in at once, in which case they must
    be the same length. Additionally, singular string keywords will be broadcast across
    all entries. As an example, if the pattern above was defined, and the keywords into
    the template were:

    keywords= {}
    keywords["Person"] = ["Jessica", "Frank", "Alicia"],
    keywords["Mentor"] = ["Michael", "Michael", "Chris"]
    keywords["year"] = 2022

    The resulting formatted string would be

    Jessica, whose mentor is Michael, has graduated in 2022 OMG!!
    Frank, whose menter is Michael, has graduated in 2022 OMG!!
    Alicia, whose mentor is Chris, has graduated in 2022 OMG!!

    """
    multifill_break_string = ";!;"
    ### Is methods. Checks details which require bool answers
    @classmethod
    def is_subtemplate(cls, item: str):
        """Checks if item represents a subtemplate with the given name"""
        #The subtemplate exists if it is a part
        #of the class with the given name which is a string
        if not hasattr(cls, item):
            return False
        if not isinstance(getattr(cls, item), str):
            return False
        return True
    @classmethod
    def is_multifill(cls, item: str):
        """Checks if item is a multifill template feature"""
        #A multifill exists if the multifill break sequence is present
        #within a format block.
        if cls.multifill_break_string in item:
            #Deliberately long for program clarity. Do not shorten to "return cls.multifill in item"
            return True
        return False
    @staticmethod
    def is_keyword(item: str, kwargs: Dict[str,str]):
        """Checks if item is a keyword defined in the kwargs dictionary"""
        if item in kwargs:
            return True
        return False


    ### Formatting Utilities. These do some of the lower level work


    @dataclasses.dataclass
    class format_string_section:
        original_format_string: str
        format_string_contents: str

    @staticmethod
    def clean_template(item: str) -> str:
        """Ensures templates which are defined in class are properly deindented"""
        return textwrap.dedent(item)
    @classmethod
    def get_format_chunks(cls, template: str)->List[format_string_section]:
        """Gets format names out of strings. Respects balancing"""
        #Does a depth based analysis to find balanced top level {} blocks.
        #Todo: Handle edge cases
        depth = 0
        start = 0
        position = 0
        outputs: List[Template.format_string_section] = []
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
                block = cls.format_string_section(target, contents)
                outputs.append(block)
        if depth != 0:
            raise RuntimeError("Lacking close } for some open {")
        return outputs

    @classmethod
    def split_mulifill_block(cls, block: str) -> Tuple[str, str]:
        """
        Splits multifill into the join string and subtemplate.
        Returns Join_String, Subtemplate
        """
        start_index = block.find(cls.multifill_break_string)
        end_index = start_index + len(cls.multifill_break_string)
        return block[:start_index], block[end_index:]


    ### Logical utilities. These control the overall flow ###
    @classmethod
    def handle_formatting_substring(cls, item: str, kwargs: Dict[str, str]):
        """
        Handles a substring from a formatting instruction.
        Retrieves and compiled a template, a keyword, or other
        instructions as appropriate
        """
        if cls.is_subtemplate(item):
            template = getattr(cls, item)
            template = cls.clean_template(template)
            try:
                return cls.compile_subtemplate(template, kwargs)
            except TemplateKeyNotFound as err:
                raise SubtemplateCompileFailure(item, template, err.name) from err
            except SubtemplateCompileFailure as err:
                raise SubtemplateCompileFailure(item, template, err.name) from err
        elif cls.is_multifill(item):
            return cls.compile_multifill(item, kwargs)
        elif cls.is_keyword(item, kwargs):
            return kwargs[item]
        else:
            raise TemplateKeyNotFound(item)
    @classmethod
    def compile_subtemplate(cls, subtemplate: str, kwargs: Dict[str, str])->str:
        """Compiles a subtemplate, by looping through and handling it's formatting blocks"""
        substitution_buffer = {}
        format_substrings = cls.get_format_chunks(subtemplate)
        for block in format_substrings:
            content = block.format_string_contents
            substitution_buffer[block.original_format_string] = cls.handle_formatting_substring(content, kwargs)


        output = subtemplate
        for key, value in substitution_buffer.items():
            output = output.replace(key, value)
        return output

    @classmethod
    def compile_multifill(cls, multifill: str, kwargs: Dict[str, str]):
        """Compiles a multifill, by looping through and handling it's subfeatures then compiling"""
        #A multifill is compiled recusively as in a subtemplate. However, before assembly,
        #lists are weaved together and the answer is then joined.

        feature_buffer = {}
        join_str, multifill_template = cls.split_mulifill_block(multifill)
        multifill_subblocks = cls.get_format_chunks(multifill_template)
        for subblock in multifill_subblocks:
            content = subblock.format_string_contents
            feature_buffer[subblock.original_format_string] = cls.handle_formatting_substring(content, kwargs)

        #Create the list and string buffer, holding respectively
        #multifill lists and standard substitution strings.
        list_buffer = {key : value for key, value in feature_buffer.items() if isinstance(value, list)}
        string_buffer = {key : value for key, value in feature_buffer.items() if not isinstance(value, list)}

        if len(list_buffer) > 0:
            #Error catching for inconsistent lengths.
            first_key = list(list_buffer.keys())[0]
            for key, value in list_buffer.items():
                if len(value) != len(list_buffer[first_key]):
                    message = "Invalid value for key. \n"
                    message = message + "Key {current_key} is of length {current_length} \n"
                    message = message + "This does not match {first_key} of length {first_length}"
                    message = message.format(current_key=key, current_length=len(value),
                                             first_key = first_key, first_length=len(list_buffer[first_key]))
                    raise ValueError(message)

        #Zip all the multifill layers together, to form individual layers.
        formatting_dictionaries = []
        multifill_layers = zip(*list(list_buffer.values()))
        for layer in multifill_layers:
            formatting_dict = dict(zip(list_buffer.keys(), layer)) if len(list_buffer) > 0 else {}
            formatting_dict.update(string_buffer)
            formatting_dictionaries.append(formatting_dict)

        #Build the feature
        output_string_buffer = []
        for format_dict in formatting_dictionaries:
            output = multifill_template.format(**format_dict)
            output_string_buffer.append(output)
        final_output = join_str.join(output_string_buffer)
        return final_output

    @classmethod
    def compile_template(cls, name: str, kwargs):
        """Compiles a particular template"""
        if not cls.is_subtemplate(name):
            raise AttributeError("No attribute with name %s found: template does not exist" % name)
        template = getattr(cls, name)
        try:
            return cls.compile_subtemplate(template, kwargs)
        except TemplateKeyNotFound as err:
            raise SubtemplateCompileFailure(name, template, err.name) from err
        except SubtemplateCompileFailure as err:
            raise SubtemplateCompileFailure(name, template, err.name) from err


class ClassRewriteTemplate(Template):
    """

    Utilized for class rewriting.

    This contains template code which syncronizes the replacement of
    a large range of features in various parts of the templates
    required - primarily the class_features, the class_instance,
    and class_wrapper rewrites.

    """
    #Magic names.

    class_feature_magic_name = "__class_feature"
    class_feature_instance_magic_name = """__class_feature_instance"""
    class_instance_magic_name = "__class_instance"
    class_wrapper_magic_name = "__class_wrapper"

    #This template is for creating the class attribute and
    #field holder. Anything which needs to accessable between
    #instances ends up created on a single by methods here

    class_feature_name = "{class_feature_magic_name}_{name}"
    class_feature_instance_name = "{class_feature_instance_magic_name}_{name}"
    class_feature_init_assignments = "{\n       ;!;self.{class_field_name} = {class_field_construction}}"
    class_feature_method_construction = """{\n    ;!;
        def {class_method_name}({class_method_parameters}):
            {class_method_code}
    }
    """
    class_feature_template = """\
    class {class_feature_name}:
        \"\"\" 
        This is an autogenerated class to handle class attributes and
        fields
        \"\"\"
        def __init__(self):
            #Autogenerated assignment code.
            {class_feature_init_assignments}
        #Class methods are located below.
        {class_feature_method_construction}
    {class_feature_instance_name} = {class_feature_name}()
    """

    #The following code consists of the sequence of template
    #information needed in order to represent the class instance rewrite.
    #
    #Many keywords are, of course, shared.

    instance_name = "{class_instance_magic_name}_{name}"

    class_attribute_properties = """\
    \n;!;    @property
        def {class_field_name}(self):
            return self.__class_features.{class_field_name}
        @{class_field_name}.setter
        def {class_field_name}(self, value):
            self.__class_features.{class_field_name} = value
    """
    instance_template = """\
    class {instance_name}:
        #class attribute property methods. Used to access class attributes safely and sanely
        {class_attribute_properties}
        #Constructor. Contains 
        def __init__({instance_self_name}, 
            class_features: {class_feature_name}, 
            {init_parameters}):
            {instance_self_name}.__class_features = {class_feature_name}
            {class_instance_init_code}
        {instance_methods}
    """

    ## The wrapper template for the class is defined below. The
    # wrapper can track environmental information and other
    # fun bits and pieces.

    wrapper_init_assignments ="""\
    {\n;!;        self.{environment} = {environment}}
    """
    wrapper_call_params = """\
    {,\n         ;!;{wrapper_init_parameter} : {wrapper_init_type}}}
    """
    from_wrapper_to_instance_params = """\
    {,\n         ;!;{wrapper_init_parameter}}
    """
    wrapper_template = """\
    class {class_wrapper_magic_name}_{name}:
        #This is designed to ensure environmental information
        #is properly accounted for, and isinstance runs right
        #
        #It is autogenerated.
        def __init__(self, {class_feature_instance_name} : {class_feature_name}, { ,;!; {environment} : {environment_types}):
            self.__class_features = {class_feature_instance_name}
            {wrapper_init_assignments}
        def __call__(self, {wrapper_call_params}):
            return {instance_name}(self.__class_features, {from_wrapper_to_instance_params})
    """
    @classmethod
    def format_class_features_template(cls, keywords: Dict[str, Union[str, List[str]]])->str:
        return cls.compile_template("class_feature_template", keywords)


keywords = {}
keywords["name"] = "test"

keywords["class_field_name"] = []
keywords["class_field_construction"] = []
ClassRewriteTemplate.format_class_features_template(keywords)






