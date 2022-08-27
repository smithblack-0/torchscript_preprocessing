import collections
import dataclasses
import enum

import regex
import textwrap
from typing import List, Tuple, Dict, Union, Optional


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

class IllegalDirective(Exception):
    """
    Occurs when something the user
    is specifying does not make any sense
    """
    def __init__(self, problem: str,  directive: str):
        message = "\nA problem existed with a specified directive: %s" % problem
        message += "The directive: \n%s" % directive
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
    and they may be passed when beginning a format. It is the
    case that a double bracket will act as an escape block as
    well. That is, something like {{'a' : 1, 'b' : 2}} will not be substituted,
    and will be changed into {'a' : 1, 'b' : 2} on format.

    -- dynamic formatting --

    certain character groupings are capable of pulling text
    dynamically out of nearby text. These commands are indicated below. They
    may be found in any template feature, and will pull from the last examined
    subtemplate.

    !#!CAPTURE_PRIOR_UNTIL(str)
    !#!CAPTURE_POST_UNTIL(str)

    ------!#!CAPTURE_PRIOR_UNTIL(str) ----

        Captures prior characters until the string in 'str' is found. Then replace
        the command with the character. Do not include capture value.

    ------- !#!CAPTURE_POST_UNTIL(str) -----
        Captures characters after the formatting region until the given string
        appears or until end of document. Then replace myself with the captured
        values. Do not include capture value.



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

    format_string_capture_pattern = regex.compile(r"{(?:(?>[^{}]+)|(?R))*\}")
    multifill_break_string = ";!;"
    format_substring_start_escape = "{{"
    format_substring_end_escape = "}}"

    command_keyword = "!#!"
    parameter_regex_template = "(?<={keyword}\()[^\s]+(?=\))"
    replace_regex_template = r"{keyword}\([^\s]+\)"

    capture_prior_until_keyword = command_keyword + "CAPTURE_PRIOR_UNTIL"
    capture_post_until_keyword =  command_keyword + "CAPTURE_POST_UNTIL"

    capture_prior_patterns = (
        capture_prior_until_keyword,
        regex.compile(parameter_regex_template.format(keyword=capture_prior_until_keyword)),
        regex.compile(replace_regex_template.format(keyword=capture_prior_until_keyword))
    )

    capture_post_patterns = (
        capture_post_until_keyword,
        regex.compile(parameter_regex_template.format(keyword=capture_post_until_keyword)),
        regex.compile(replace_regex_template.format(keyword=capture_post_until_keyword))
    )

    @dataclasses.dataclass
    class formatting_directive:
        """
        Represents a single identified formatting directive
        located within a broader source context
        """
        start_index: int
        end_index: int
        source_template: str
        raw_substring: str
        trimmed_substring: str

    class dynamic_keywords(enum.Enum):
        capture_prior_until = "#"

    ### Is methods. Checks details which require bool answers
    @classmethod
    def is_subtemplate(cls, item: formatting_directive)->bool:
        """Checks if item represents a subtemplate with the given name"""
        #The subtemplate exists if it is a part
        #of the class with the given name which is a string
        if not hasattr(cls, item.trimmed_substring):
            return False
        if not isinstance(getattr(cls, item.trimmed_substring), str):
            return False
        return True
    @classmethod
    def contains_command(cls, item: formatting_directive)->bool:
        """Checks if there is a command which needs to be handled."""
        keyword, _, _ = cls.capture_prior_patterns
        if keyword in item.trimmed_substring:
            return True

        keyword, _, _ = cls.capture_post_patterns
        if keyword in item.trimmed_substring:
            return True
        return False

    @classmethod
    def is_multifill(cls, item: formatting_directive)->bool:
        """Checks if item is a multifill template feature"""
        #A multifill exists if the multifill break sequence is present
        #within a format block.
        if cls.multifill_break_string in item.trimmed_substring:
            #Deliberately long for program clarity. Do not shorten to "return cls.multifill in item"
            return True
        return False
    @staticmethod
    def is_keyword(item: formatting_directive, kwargs: Dict[str,str])->bool:
        """Checks if item is a keyword defined in the kwargs dictionary"""
        if item.trimmed_substring in kwargs:
            return True
        return False


    ### Formatting Utilities. These do some of the lower level work


    @staticmethod
    def clean_template(item: str) -> str:
        """Ensures templates which are defined in class are properly deindented"""
        return textwrap.dedent(item)

    @classmethod
    def get_formatting_directives(cls,
                                  template: str,
                                  context: Optional[formatting_directive]=None)->Tuple[str, List[formatting_directive]]:
        """Gets format names out of strings. Respects balancing. Maintains
        context information regarding what is being compiled in the broader template and
        where.

        :param template: A template from which to get the substrings
        :returns: A escaped format string, and a list of the formatting substrings dataclasses
        """

        #Does a depth based analysis to find balanced top level {} blocks.
        outputs: List[Template.formatting_directive] = []
        escaped_template = template
        for match in regex.finditer(cls.format_string_capture_pattern, template):
            if context is None:
                context_template = template
                start_index, end_index = match.regs[0]
            else:
                start_index = context.start_index
                end_index = context.end_index
                context_template = context.source_template
            substring = match.string[start_index:end_index]
            trimmed_string = substring[1:-1]
            if substring.startswith(cls.format_substring_start_escape) \
                and substring.endswith(cls.format_substring_end_escape):
                #Replace the escaped instance
                escaped_template = escaped_template.replace(substring, trimmed_string)
            else:
                #Append the formatting package for further work.
                format_package = cls.formatting_directive(start_index,
                                                          end_index,
                                                          context_template,
                                                          substring,
                                                          trimmed_string)
                outputs.append(format_package)
        return escaped_template, outputs

    @classmethod
    def split_multifill_directive(cls, block: formatting_directive) -> Tuple[str, str]:
        """
        Splits multifill into the join string and subtemplate.
        Returns Join_String, Subtemplate
        """
        trimmed_string = block.trimmed_substring
        start_index = trimmed_string.find(cls.multifill_break_string)
        end_index = start_index + len(cls.multifill_break_string)
        return block[:start_index], block[end_index:]


    ### Logical utilities. These control the overall flow ###
    @classmethod
    def handle_formatting_directive(cls, directive: formatting_directive, kwargs: Dict[str, str]):
        """
        Handles a identified user formatting directive.
        Retrieves and compiled a template, a keyword, or other
        instructions as appropriate. Handles errors
        elegantly for maximum information.
        """
        if cls.is_subtemplate(directive):
            template = getattr(cls, directive.trimmed_substring)
            try:
                return cls.compile_subtemplate(template, kwargs)
            except TemplateKeyNotFound as err:
                raise SubtemplateCompileFailure(directive.trimmed_substring, template, err.name) from err
            except SubtemplateCompileFailure as err:
                raise SubtemplateCompileFailure(directive.trimmed_substring, template, err.name) from err
        elif cls.contains_command(directive):
            directive = cls.compile_command(directive)
        elif cls.is_multifill(directive):
            return cls.compile_multifill(directive, kwargs)
        elif cls.is_keyword(directive, kwargs):
            return kwargs[directive.trimmed_substring]
        else:
            raise TemplateKeyNotFound(directive.trimmed_substring)
    @classmethod
    def compile_subtemplate(cls, directive: formatting_directive, kwargs: Dict[str, str])->str:
        """Compiles a subtemplate, by looping through and handling it's formatting blocks"""
        subtemplate = getattr(cls, directive.trimmed_substring)
        substitution_buffer = {}
        subtemplate, format_substrings = cls.get_formatting_directives(subtemplate)
        for directive in format_substrings:
            substitution_buffer[directive.raw_substring] = cls.handle_formatting_directive(directive, kwargs)

        output = subtemplate
        for key, value in substitution_buffer.items():
            output = output.replace(key, value)
        return output
    @classmethod
    def compile_command(cls, command_directive: formatting_directive):
        """Handles dynamic commands which have been issued. """
        substring = command_directive.trimmed_substring

        keyword, parameter_pattern, replace_pattern = cls.capture_prior_patterns
        if keyword in substring:
            #Handle prior until preprocessing.

            #Find all the cases, then begin compilation process.
            #Do this by looking into the command directive for where
            #the current format block starts, and then work backwards
            #until the parameter is seen. When this happens, capture
            #everything up to the parameter, then replace self with
            #capture.
            replacement_buffer = {}
            parameters = regex.findall(parameter_pattern, substring)
            to_replace = regex.findall(replace_pattern, substring)
            for parameter, to_replace in zip(parameters, to_replace):



            for match in regex.finditer(


    @classmethod
    def compile_multifill(cls, multifill_directive: formatting_directive, kwargs: Dict[str, str]):
        """Compiles a multifill, by looping through and handling it's subfeatures then compiling"""
        #A multifill is compiled recusively as in a subtemplate. However, before assembly,
        #lists are weaved together and the answer is then joined.

        feature_buffer = {}
        join_str, multifill_template = cls.split_multifill_directive(multifill_directive)
        multifill_template, multifill_subblocks = cls.get_formatting_directives(multifill_template, multifill_directive)
        for subblock in multifill_subblocks:
            feature_buffer[subblock.raw_substring] = cls.handle_formatting_directive(subblock, kwargs)

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
        template = cls.clean_template(template)
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
