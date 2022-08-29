import collections
import dataclasses
import enum
import regex
import textwrap
import pyparsing as pp
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
    def __init__(self, problem: str,  directive: "Directive"):
        message = "\nA problem existed with a specified directive: %s" % problem
        message += "The directive: \n%s" % directive.entire_directive
        self.directive = directive
        super().__init__(message)

class TemplateKeyNotFound(Exception):
    def __init__(self, name: str, directive: "Directive"):
        self.name = name
        self.directive = directive
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
    templates: "Template"
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
                 templates: "Template",
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
    select_indicators: A tuple of two strings. an example would be ('{','}'). These
        indicate what is actually a directive. Must be defined
    selection_grammer: A List of strings and none.
        Strings must match exactly. They will be ignored.
        None may be any string. They will be captured.

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
    #Directive type provides the context info
    #The token magic word should be a unique phrase, connected to the token. It is used
    #to negate collisions
    #T

    directive_type: str
    token_magic_word: str
    subgroup_patterns = List[Optional[str]]
    select_indicators: Tuple[str, str]

    #Utility and language definitions. Do not override unless you are sure what you are doing.

    subgroup_delimiter: str = "|=|"
    token_indicators: Tuple[str, str] = ("<####", "####>") #Found in return string

    #Class methods .Concerned primarily with creating and processing the
    #dataclass instances.

    @classmethod
    def get_select_pattern(cls)->pp.ParserElement:
        """
        A compiled parser pattern.

        This pattern will match the syntax of an
        embedded keyword or command for python.
        """
        #This functions as follows.
        #
        #First, we start up a pyparsing pattern
        #on the open block. Then, for each
        #subgrammer feature, we append it
        #along with a suppressed join block.

        open, close = cls.select_indicators
        subgroup_delimitor = cls.subgroup_delimiter
        pattern = pp.Literal(open)
        for i, grammer in enumerate(cls.subgroup_patterns):
            # Handle delimiter
            if i > 0:
                pattern = pattern + pp.Suppress(pp.Literal(subgroup_delimitor))

            # Handle grammer case
            if grammer is None:
                pattern = pattern + ...  # Capture useful info
            else:
                pattern = pattern + pp.Suppress(pp.Literal(grammer))  # Part of syntax, but not parameters.
        pattern = pattern + pp.Literal(close)
        return pattern

    @classmethod
    def string_has_match(cls, string: str)->bool:
        """ Checks if it is the case that a match currently exists in the given string"""
        pattern = cls.get_select_pattern()
        for match in pattern.scan_string(string):
            return True
        return False

    @classmethod
    def get_token(cls, number)->str:
        """Get token representing 'number' entity"""
        startwith, endwith = cls.token_indicators
        return startwith + cls.token_magic_word + str(number)+ endwith

    @classmethod
    def get_directives(cls, string: str, predicate: Optional[Callable[["Directive"], bool]] = None)->Tuple[str, Dict[str, "Directive"]]:
        """
        This particular method does two primary tasks. These are:

        * Escape extracted selections out of string under processing
        * Return a dictionary mapping escape tokens to the found internal
          content.
        * If defined, will get subgroups as well.

        :param string: A string to extract directives from
        :param predicate: A predicate to evaluate a directive based on. False means do not use.
        :returns
            * A escaped example of string. Matching directives are replaced with a token
            * A dictionary mapping tokens to instances containing the disassembled features
        """

        if predicate is None:
            predicate = lambda x : True

        pattern = cls.get_select_pattern()
        token_counter = 0
        token_map: Dict[Tuple[int,int], str] = {}
        directives_dict: Dict[str, "Directive"] = {}
        for match in pattern.scan_string(string):

            #Get the required features.
            #
            # These are the open string, the close string,
            # the content string, the token, and the subgroups.

            open_str, close_str = cls.select_indicators
            subgroups, startat, endat = match
            content_startat = startat + len(open_str)
            content_endat = endat -len(close_str)
            content = string[content_startat:content_endat]
            entire = string[startat:endat]
            token = cls.get_token(token_counter)
            directive = Directive(token,
                                  entire,
                                  open_str,
                                  content,
                                  close_str,
                                  subgroups
                                  )
            if predicate(directive):
                directives_dict[token] = directive
                token_map[(startat, endat)] = token
                token_counter += 1

        #Update the string. Insert the tokens
        #by cutting out the relevant chunks
        #as we go along.
        original_string = string
        output_string = ""
        pos = 0
        for (startat, endat), token in token_map.items():
            unaltered_segment = original_string[pos:startat]
            update = unaltered_segment + token
            output_string += update
            pos = endat
        if pos != len(output_string):
            unaltered_segment = original_string[pos:len(output_string)]
            output_string += unaltered_segment

        return output_string, directives_dict

    @classmethod
    def compile_directives(self,
               context: Context,
               string: str,
               parser: Callable[[Context,str], str])->Tuple[str, Dict[str, str]]:
        """
        Compiles the directives in a particular incoming string.
        The current context and the parser function must be provided,
        allowing for compilation of subcomponents if desired.

        Implimented by subclass.
        :param string:
        :return:
            * str - a tokenized string
            * Dict[str, str] - a mapping of tokens to their equivalents. Ready for a .format call.
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





### Basic Formatting Language
#
# The basic formatting language is designed
# to basically reproduce the behavior of python,
# with a few extra twists. It is indicated
# by starting a {}, and has only one entry inside.
#
# Keywords and Subtemplates are valid targets for
# lookup.

class NativeDirectiveParser(Directive):
    """
    Quite capable of handling native python
    code, the native parser simply uses a
    {} edge delimiter
    """
    select_indicators = ("{", "}")


class EscapeDirective(Directive):
    """
    An escape directive

    Represents a section in which
    escaped characters can be found.

    The directive will essentially run first,
    and then be set aside for later.
    """

    directive_type = "Escape"
    token_magic_word =  "ESCAPE"
    select_indicators = ("{{", "}}")
    final_indicators = ("{", "}")
    subgroup_patterns = (None)

    @classmethod
    def compile_directives(cls,
               context: Context,
               string: str,
               parser: Callable[[Context,str], str])->Tuple[str, Dict[str, str]]:
        #Slice out escaped content. Run parser.
        #Place escaped content into position.
        start, end = cls.final_indicators
        output_string, directives = cls.get_directives(string)
        token_map = {token : start+ directive.content + end
                               for token, directive in directives.items()
                               }
        return output_string, token_map

class Lookup(NativeDirectiveParser):
    """
    A representation of a
    keyword or subtemplate lookup.

    Will identify if they are in a provided
    string, and go about formatting them if found.
    """
    directive_type = "Keyword"
    token_magic_word = "KEYWORD"
    subgroup_patterns = (None,)
    @classmethod
    def compile_directives(cls,
               context: Context,
               string: str,
               parser: Callable[[Context,str], str])->Tuple[str, Dict[str, str]]:
        output_string, directives = cls.get_directives(string)
        formatting = {}
        for token, directive in directives.items():
            if directive.content in context.templates:
                subtemplate = context.templates[directive.content]
                subcontext = context.derive_from_template(subtemplate)
                formatting[token] = parser(subcontext, subtemplate)
            elif directive.content in context.keywords:
                formatting[token] = context.keywords[directive.content]
            else:
                raise TemplateKeyNotFound(directive.content, directive)
        return output_string, formatting

#### ADVANCED LANGUAGE ####
#
# The advanced language is designed to perform
# addition useful features when dealing with templates.
#
# They generally will go off recursively, and will
# go off before anything else.

class AdvancedDirectiveParser(Directive):
    """
    The advanced template language
    is designed to enable some level of
    programmable relational control
    among elements lying around nearby

    These elements are allowed to
    use context and python code to
    do otherwise weird things
    """
    select_indicators = ("<!!", "!!>")

class FormatMultifill(AdvancedDirectiveParser):
    """
    Multifill formatting is performed by opening a format block and placing inside it
    two string sections, consisting of the join string and the multifill template. The
    two sections should be separated by the delimitor, which is '|=!' by default. An
    example might be:

    <!!MULTISPLIT->OMG!!!\n|=| {Person}, whose mentor is {Mentor}, has graduated in {year}!!>

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

    'Jessica, whose mentor is Michael, has graduated in 2022 OMG!!
    Frank, whose menter is Michael, has graduated in 2022 OMG!!
    Alicia, whose mentor is Chris, has graduated in 2022 OMG!!!'
    """
    directive_type = "Multifill"
    token_magic_word= "MULTIFILL"
    formatting_select_indicators = ("{", "}")
    subgroup_patterns = ("MULTIFILL", None, None)

    @classmethod
    def compile_directives(cls,
               context: Context,
               string: str,
               parser: Callable[[Context,str], str])->Tuple[str, Dict[str, str]]:

        output_string, directives = cls.get_directives(string)
        formatting = {}
        for token, directive in directives.items():
            #Things are a little complex here, so let's add some exposition.
            #
            #Basically, we claim the keywords within our chunk to prevent
            #something else from filling them in as a list directly
            #
            #After normal compilation is complete, we then go ahead and
            #fetch said keywords to perform a multifill

            subcontext = context.derive_from_directive(output_string, directive)
            _, _, join_str, repeat_feature, _ = directive.subgroups
            repeat_feature, claimed_keywords = Keyword.get_directives(repeat_feature)
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
        return output_string, formatting


class ReplicateIndent(AdvancedDirectiveParser):
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
               parser: Callable[[Context,str], str]) ->Tuple[str, Dict[str, str]]:

        output_string, directives = cls.get_directives(string)
        formatting = {}
        for token, directive in directives.items():
            if context.start_token_loc is None:
                # Handle raw replicate indent. If someone wants to use
                # one for whatever reason???
                endpoint = output_string.index(token)
            else:
                endpoint = context.start_token_loc
            startpoint = output_string.rfind("\n", 0, endpoint)
            if startpoint == -1:
                #Hit start of line
                startpoint = 0
            indent_string = output_string[startpoint:endpoint]
            formatting[token] = indent_string
        return output_string, formatting


def Parser(context: Context, string: str,)->str:
    """
    The parsers job is to go
    through it's list, collect the formatting items
    as it goes, and then reverse the process to
    build the result.

    :param string: The string to parse
    :param context: A context package. Not used by parser, but passed into
        directive parsers
    :return: The parsed string
    """
    #NOTE TO MAINTAINERS:
    #
    # In order to add new elements to the template
    # language, all that you need to do is
    # add it in this list. Make sure your
    # priority is right, though.

    resolution_sequence = (
        EscapeDirective,
        FormatMultifill,
        ReplicateIndent,
        Lookup
    )

    #Parse everything moving forward
    token_restore_stack = []
    for DirectiveParser in resolution_sequence:
        if DirectiveParser.string_has_match(string):
            try:
                string, formatting = EscapeDirective.compile_directives(context, string, Parser)
                token_restore_stack.append(formatting)
            except SubtemplateCompileFailure as err:
                raise err

    #Substitute in tokens
    token_restore_stack.reverse()
    for token_formatting in token_restore_stack:
        string = string.format(**token_formatting)
    return string



class Template():
    """
    A template is a place one
    can drop a whole bunch of different
    subtemplates, and use them to parse
    the template in light of keyword information

    It supports quite a few different features.

    It should be used by subclassing, defining
    as class attributes the subtemlates,
    and then calling the parse function
    with a given collection of keywords

    The class will then proceed to parse
    the information, yielding useful error
    info as it goes.
    """



    @staticmethod
    def clean_template(item: str) -> str:
        """Ensures templates which are defined in class are properly deindented"""
        return textwrap.dedent(item)

    def __contains__(self, key: str)->bool:
        """Checks if we contain the indicated feature. Makes template behave something like a list"""
        if not hasattr(self, key):
            return False
        if not isinstance(hasattr(self, key), str):
            return False
        return True

    def __getitem__(self, item)->str:
        """Allows for getting subtemplates by name, if they exist"""
        return getattr(self, item)

    def parse(self, name: str, keywords: Dict[str, str]):
        """
        Parse the indicated subtemplate using
        the keywords provided.

        :param name: The name of the template to parse
        :param keywords: The keywords to utilize.
        :return: The parsed template.
        """
        primary_template = self[name]
        context = Context(keywords, self, primary_template)
        return Parser(context, primary_template)


