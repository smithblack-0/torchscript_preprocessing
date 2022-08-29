import collections
import dataclasses
import enum

import regex
import textwrap
from typing import List, Tuple, Dict, Union, Optional, Callable


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


class Context():
    """
    A context consists of a certain string and information on what is
    currently being worked on. A context is created by providing a current
    string and a token being worked on. Notably, the various contexts can
    be derived from each other. This forms them into a linked list leading
    to the top level context.

    The context will subsequently display information such as where the
    token under construction starts,ends, and what was used to construct it.

    """
    parent: "Context"
    source_string: str
    directive_type: str
    start_token_loc: int
    end_token_loc: int
    keywords: Dict[str, str]
    templates: Dict[str, str]
    def derive_from_directive(self, source_string: str, directive: "Directive")->"Context":
        """
        Create a new context with the current context as a parent.

        :param source_string: The claimed-token source string to draw from
        :param directive: The directive which was created from said source
        :return: A context, which will posses the current context as a parent
        """
        start = source_string.index(directive.token)
        end = start + len(directive.token)
        return Context(
            self.keywords,
            self.templates,
            source_string,
            self,
            start,
            end
        )
    def derive_from_template(self, source_string: str)->"Context":
        """
        Create a new context on a new template, but with a
        link back to the old one.

        :param source_string: The brand new source.
        :return: A context feature
        """
        return Context(
            self.keywords,
            self.templates,
            source_string,
            self
        )
    def __init__(self,
                 keywords: Dict[str, str],
                 templates: Dict[str, str],
                 source_string: str,
                 parent: Optional["Context"] = None,
                 start_token_loc: Optional[int] = None,
                 end_token_loc: Optional[int] = None
                 ):
        self.keywords = keywords
        self.templates = templates
        self.source_string = source_string
        self.parent = parent
        self.start_token_loc = start_token_loc
        self.end_token_loc = end_token_loc

class Directive():
    """
    A directive does something, and
    is responsible for a particular group of
    compilation tasks. This is the abstract
    class for the directive type.

    The class code located here is basically all
    command parser code. Code is parsed by a traveling
    mechanism, in which sections of a string under examination
    are replaced with token representations and the command
    features returned attached to an object.

    It is up to the subclass to impliment methods which finish any
    parsing job which is occurring.

    Notably:
    * A directive has much logic operating at the class level. This logic is responsible
      for creating particular instances of itself which carry needed information.
    * A directive must have a open character and a close character, indicated by
        the two values in the formatting select indicator class property tuple.
        The region between two of these is known as a formatting block.
    * A directive may have any number of subcommands placed in the formatting block
        These will automatically be separated from each other, and fed in sequence
        as keywords based on subgroups name on initialization.


    --- class attributes ---

    REQUIRED:

    directive_type: A unique string, used for context, indicating what type of thing this is. Must
        be defined
    token_magic_word: A string indicating what kind of token the generated tokens are. Must be defined
    formatting_select_indicators: A tuple of two strings. an example would be ('{','}'). These
        indicate what is actually a directive. Must be defined

    OPTIONAL:

    subgroup_split_keyword: Indicates what string to split on when making subgroups
        For instance, '-' between sections.
    subgroup_split_pattern: A list of string, none entities.
        String entities much match among the split groups. Meanwhile, none
        entities may represent anything.

        For example, to capture Directives of format #Command-Do-Condition, where
        condition is what we care about, we could split on '-' and use
        ("Command", "Do", "Condition").

        Anything not seen as this will not be correctly matched.

    """
    #Class requirmements for functionality
    #
    #Tokens should be unique to avoid collisions.

    directive_type: str
    token_magic_word: str
    subgroup_patterns = List[Optional[str]]
    formatting_select_indicators: Tuple[str, str]

    #Utility and language definitions. Do not override unless you are sure what you are doing.

    formatting_token_indicators: Tuple[str, str] = ("<!!##", "##!!>") #Found in return string
    subgroup_split_keyword: str = "->"

    regex_input_capture_template = r"([^{open}{close}]*+(?:(?R))*+[^{open}{close}]*)" #Recursively ignores nested {}
    regex_specific_capture_template = r"({name})"#Captures a particular word
    regex_general_capture = r"({open}){select}({close})" #Captures the entire sequence, and everything interesting.

    #Class methods .Concerned primarily with creating and processing the
    #dataclass instances.
    @property
    @classmethod
    def select_pattern(cls)->regex.Pattern:
        """
        A compiled regex pattern.

        The pattern will find and match the open
        and closing parenthesis, along with all contained keyword content.
        """

        open, close = cls.formatting_select_indicators
        input_capture = cls.regex_input_capture_template.format(open=open, close=close)
        select = [input_capture if subgroup_pattern is None
                  else cls.regex_specific_capture_template.format(name=subgroup_pattern)
                  for subgroup_pattern in cls.subgroup_patterns]
        select = cls.subgroup_split_keyword.join(select)
        pattern = cls.regex_general_capture.format(open=open,
                                               select=select,
                                               close=close)
        pattern = regex.compile(pattern)
        return pattern

    @classmethod
    def string_contains_potential_match(cls, string: str)->bool:
        """ Checks if it is the case that a match currently exists in the given string"""
        if regex.match(cls.select_pattern, string) is None:
            return False
        return True
    @classmethod
    def get_token(cls, number)->str:
        """Get token representing 'number' entity"""
        startwith, endwith = cls.formatting_token_indicators
        return startwith + cls.token_magic_word + str(number)+ endwith
    @classmethod
    def get_directives(cls, string: str, predicate: Optional[Callable[["Directive"], bool]] = None)->Tuple[str, Dict[str, "Directive"]]:
        """
        This particular method does two primary tasks. These are:

        * Escape extracted selections out of string under processing
        * Return a dictionary mapping escape tokens to the found internal
          content.
        * If defined, will get subgroups as well.

        :returns
            * A escaped example of string. Matching directives are replaced with a token
            * A dictionary mapping tokens to instances containing the disassembled features
        """
        if predicate is None:
            predicate = lambda x : True

        def get_substring(string: str, region: Tuple[int, int]):
            start, end = region
            return string[start:end]

        pattern = cls.select_pattern
        mutating_string = string
        directives_dict: Dict[str, "Directive"] = {}

        token_counter = 0
        pos = 0
        while cls.string_contains_potential_match(mutating_string):
            match = regex.match(pattern, mutating_string, pos=pos)
            entire_region = match.regs[0]
            start_region = match.regs[1]
            end_region = match.regs[-1]
            content_regions = match.regs[2:-1]

            #Here, we figure out what the escaped token will look like,
            #then go append the normal start and end tokens to the
            #content. This is put in a dictionary, which can later be
            #fed into .format

            token = cls.get_token(token_counter)
            matched_string = get_substring(match.string, entire_region)
            start_string = get_substring(match.string, start_region)
            end_string = get_substring(match.string, end_region)
            content = get_substring(match.string, (start_region[1], end_region[0]))
            subgroups = []
            for content_region in content_regions:
                subgroups.append(get_substring(content_region, match.string))

            #Store away the instanced directive, with the command information
            directive_representation = Directive(token,
                                                 matched_string,
                                                 start_string,
                                                 content,
                                                 end_string,
                                                 subgroups)

            #If the predicate is not happy, go onto the next
            #one.
            if predicate(directive_representation)
                directives_dict[token] = directive_representation

                #Replace match with token in original string. Continue
                #using updated string.

                start, end = entire_region
                prior_string, post_string = match.string[:start], match.string[end:]
                mutating_string = prior_string + token + post_string
                pos = start +len(token)
                token_counter += 1

            else:
                start, end = entire_region
                pos = end
        return mutating_string, directives_dict

    @classmethod
    def compile_directives(self,
               context: Context,
               string: str,
               parser: Callable[[Context,str], str])->str:
        """
        Compiles the directives in a particular incoming string.
        The current context and the parser function must be provided,
        allowing for compilation of subcomponents if desired.

        Implimented by subclass.
        :param string:
        :return:
        """
        raise NotImplementedError("Must impliment format for proper functionality")
    def __init__(self, token, entire_directive, start_string, content, end_string, subgroups):

        #Sanity checking, to verify the class is setup correctly
        assert hasattr(self, "directive_type"), "Must define 'directive_type' for directive"
        assert hasattr(self, "token_magic_word"), "Must defined '"
        directive_type: str
        token_magic_word: str
        formatting_select_indicators: Tuple[str, str]

        #Store datatypes

        self.token = token
        self.entire_directive = entire_directive
        self.start_string = start_string
        self.content = content
        self.end_string = end_string
        self.subgroups = subgroups

### Advanced Formatting Language
#
# Formatting directives are generally responsible
# for keyword and context free substition task. This
# is distinct from a Context directive, which
# requires a broader context to function.

class FormattingEscapeDirective(Directive):
    """
    An escape directive

    Represents a section in which
    escaped characters can be found.

    The directive will essentially run first,
    and then be set aside for later.
    """

    directive_type = "Escape"
    token_magic_word =  "ESCAPE"
    formatting_select_indicators = ("{", "}")
    subgroup_patterns = ("ESCAPE", None)

    @classmethod
    def compile_directives(cls,
               context: Context,
               string: str,
               parser: Callable[[Context,str], str]) ->str:
        #Slice out escaped content. Run parser.
        #Place escaped content into position.
        start, end = cls.formatting_select_indicators
        revised_string, directives = cls.get_directives(string)
        revised_string = parser(context, revised_string)
        output_string = revised_string.format({token : start+ directive.content + end
                               for token, directive in directives.items()
                               })
        return output_string

class FormattingKeywordDirective(Directive):
    """
    A representation capable of handling
    a formatting keyword.

    Keywords are found in the keyword context,
    and are identified by their pattern of
    {keyword}
    """
    directive_type = "Keyword"
    token_magic_word = "KEYWORD"
    formatting_select_indicators = ("{", "}")
    subgroup_patterns = (None,)

    @classmethod
    def compile_directives(cls,
               context: Context,
               string: str,
               parser: Callable[[Context,str], str]) ->str:
        predicate = lambda directive: directive.content in context.keywords
        revised_string, directives = cls.get_directives(string, predicate)
        revised_string = parser(context, revised_string)
        formatting = {}
        for token, directive in directives.items():
            formatting[token] = context.keywords[directive.content]
        return revised_string.format(**formatting)

class FormattingSubtemplateDirective(Directive):
    """
    A directive identified by being
    a keyword like object, and being
    a template found in templates
    in the context.
    """
    directive_type = "Subtemplate"
    token_magic_word = "SUBTEMPLATE"
    formatting_select_indicators = ("{", "}")
    subgroup_patterns = (None,)

    @classmethod
    def compile_directives(cls,
               context: Context,
               string: str,
               parser: Callable[[Context,str], str]) ->str:

        predicate = lambda directive: directive.content in context.templates
        revision_string, directives = cls.get_directives(string, predicate)
        formatting = {}
        for token, directive in directives.items():
            subtemplate = context.templates[directive.content]
            subcontext = context.derive_from_template(subtemplate)
            formatting[token] = parser(subcontext, subtemplate)
        output_string = revision_string.format(**formatting)
        return output_string


class FormattingMultifillDirective(Directive):
    """
    Multifill formatting is performed by opening a format block and placing inside it
    two string sections, consisting of the join string and the multifill template. The
    two sections should be separated by the multifill_break_string, which by default
    is ';!;'. An example would be:

    {MULTISPLIT->OMG!!!->\n;!; {Person}, whose mentor is {Mentor}, has graduated in {year}}

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
    Alicia, whose mentor is Chris, has graduated in 2022 OMG!!!
    """
    directive_type = "Multisplit"
    token_magic_word= "MULTISPLIT"
    formatting_select_indicators = ("{", "}")
    subgroup_patterns = ("MULTISPLIT", None, None)

    @classmethod
    def compile_directives(cls,
               context: Context,
               string: str,
               parser: Callable[[Context,str], str]) ->str:

        revised_string, directives = cls.get_directives(string)
        formatting = {}
        for token, directive in directives.items():
            #Things are a little complex here, so let's add some exposition.
            #
            #Basically, we claim the keywords within our chunk to prevent
            #something else from filling them in as a list directly
            #
            #After normal compilation is complete, we then go ahead and
            #fetch said keywords to perform a multifill

            subcontext = context.derive_from_directive(revised_string, directive)
            _, _, join_str, repeat_feature, _ = directive.subgroups
            repeat_feature, claimed_keywords = FormattingKeywordDirective.get_directives(repeat_feature)
            join_str = parser(subcontext, join_str)
            repeat_feature = parser(subcontext, join_str)
            repeat_feature.format({token : directive.entire_directive for token, directive in claimed_keywords.items()})

            #Having done standard parsing, go fetch lists and perform the multifill

            keywords = {directive.content : context.keywords[directive.content] for directive in claimed_keywords.values()}
            list_keywords: Dict[str, List[str]] = {key : value for key, value in keywords.items() if isinstance(value, list)}
            string_keywords: Dict[str, str] = {key : value for key, value in keywords.items() if isinstance(value, str)}

            if len(list_keywords) > 0:
                #Verify lengths are sane
                standard_length = len(next(iter(list_keywords.values())))
                if not all(len(l) == standard_length for l in list_keywords.values()):
                    message = "Not all lists are of the same length"
                    raise IllegalDirective(message, directive)


                #Broadcast string keywords into list keywords
                #Create subcases for str.join.
                list_keywords.update({key : [value]*standard_length for key, value in string_keywords})

                instances = []
                for i in range(standard_length):
                    subformatting = {key : value[i] for key, value in list_keywords.items()}
                    instance = repeat_feature.format(**subformatting)
                    instances.append(instance)

                #Join and store.
                formatting[token] = join_str.join(instances)
            else:
                message = "Attempt to do a multifill with no list quantities. Use a keyword instead"
                raise IllegalDirective(message, directive)

#### ContextDirectives ####
# Context directives generally perform some sort of
# self replacement action based on the context,

class ReplicateIndent(Directive):
    """
    A context directive.

    Replaces itself with the indent up
    to the prior context region, starting
    from the front of the token definition.

    If placed in a raw template, will function
    as expected. If placed in a formatting
    subblock, will begin scanning at the start
    of the subblock and will then work backwards.

    The raw command is

    <!!ReplicateIndent!!>
    """
    directive_type = "ReplicateIndent"
    token_magic_word= "REPINDENT"
    formatting_select_indicators = ("<!!", "!>>")
    subgroup_patterns = ("ReplicateIndent")

    @classmethod
    def compile_directives(cls,
               context: Context,
               string: str,
               parser: Callable[[Context,str], str]) ->str:

        revision_string, directives = cls.get_directives(string)
        formatting = {}
        for token, directive in directives.items():
            if context.start_token_loc is None:
                # Handle raw replicate indent. If someone wants to use
                # one for whatever reason???
                endpoint = revision_string.index(token)
            else:
                endpoint = context.start_token_loc
            startpoint = revision_string.rfind("\n", 0, endpoint)
            if startpoint == -1:
                #Hit start of line
                startpoint = 0
            indent_string = revision_string[startpoint:endpoint]
            formatting[token] = indent_string
        output_string = revision_string.format(**formatting)
        return output_string



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

    multifill_break_string = ";!;"


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
