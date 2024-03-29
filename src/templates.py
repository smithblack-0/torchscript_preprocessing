import collections
import dataclasses
import enum
import regex
import textwrap
import pyparsing as pp
from typing import List, Tuple, Dict, Union, Optional, Callable, Any


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
    keywords: Dict[str, Union[str, List[str]]]
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
    def derive_from_keywords(self, keywords: Dict[str, Union[str, List[str]]])->"Context":
        """
        Create a context with the existing parameters, but with the
        additional specification that certain keywords may be replaced with new values
        :param keywords: The keywords to use from now on
        :return: A new context
        """
        final_keywords = self.keywords.copy()
        final_keywords.update(keywords)
        return Context(
            final_keywords,
            self.templates,
            self.source_string,
            self,
            self.start_token_loc,
            self.end_token_loc
        )

    def __init__(self,
                 keywords: Dict[str, Union[str, List[str]]],
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

class Keyword_Alias:
    """
    This is an aliasing class. It is designed
    to enable some other class to take over
    final substution of keywords from other
    classes by aliasing the keyword in the context
    and allowing later substitution of, and final resolution
    of, keywords.

    Logicwise, it essencially jukes out the keywords by ensuring
    they will be strings, nothing else.
    """
    alias_indicators = ("<$$", "$$>")
    @classmethod
    def claim_alias(cls, context: Context, magic_word: str)->Tuple[Context, "Keyword_Alias"]:
        """
        Setup a new context with an alias connection.

        :param context: The context to make an alias from
        :param magic_word: A string unique to this kind of alias
        :return: An Alias context, and a Keyword_Alias to manipulate the base string
        """
        original_keywords = context.keywords
        updated_keywords = {}
        alias_mappings = {}
        open_delimitor, close_delimiter = cls.alias_indicators
        for i, (key, value) in enumerate(original_keywords.items()):
            alias_value = open_delimitor + magic_word + str(i) + close_delimiter
            updated_keywords[key] = alias_value
            alias_mappings[alias_value] = value

        updated_context = context.derive_from_keywords(updated_keywords)
        keyword_alias = cls(updated_keywords, alias_mappings)
        return updated_context, keyword_alias
    def find_aliases_in_string(self, string: str)->List[str]:
        """
        This method will look through a string and detect,
        for each known alias feature, if that feature
        is present in the string. It will return a list
        of detected features.

        :param string: The string to examine
        :return: A list of dectected aliases
        """


        output = []
        lookup_dict = dict(zip(self.keyword_updates.values(), self.keyword_updates.keys()))
        for key in self.aliasing.keys():
            if key in string:
                original_keyword = lookup_dict[key]
                output.append(original_keyword)
        return output

    def substitute(self, string: str, keywords: Optional[Dict[str, str]]=None)->str:
        """
        Using the stored alias knowledge,
        substitute in corrosponding aliases into string.

        If a keywords is specified, substitute that. Else,
        substitute the original value

        :param string: The string to substitute into
        :param keywords: The keywords to substitute
        :return: A restored string
        """

        updates = {self.keyword_updates[key] : value for key, value in keywords.items()}
        restoration = self.aliasing.copy()
        restoration.update(updates)
        for key, value in restoration.items():
            string = string.replace(key, value)
        return string

    def __init__(self, updated_keywords: Dict[str, str], alias_mappings: Dict[str, Any]):
        self.keyword_updates = updated_keywords
        self.aliasing = alias_mappings

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

        #Develop parsing literals for the delimiters
        open_delimiter, close_delimiter = cls.select_indicators
        open_delimiter = pp.Literal(open_delimiter)
        close_delimiter = pp.Literal(close_delimiter)
        subgroup_delimitor = pp.Literal(cls.subgroup_delimiter)

        #Develop recursive ignore expression. This allows a nested
        #command, such as <!!Do something|=|<!!REPLICATEINDENT!!>!!>
        #to parse by finding and ignoring balanced delimiters

        nested_skip = pp.Forward()
        ignore_recursion = open_delimiter + pp.SkipTo(close_delimiter, ignore=nested_skip) + close_delimiter
        nested_skip <<= ignore_recursion

        ## Compile the subgroups
        #
        # For each subgroup, if the current element is
        # none, we setup a skipto which captures all the internal
        # content ignoring balanced delimitators and skipping to the next
        # group delimitor. This captures everything in between
        #
        # Meanwhile, if it is not none, we just ignore the word as part
        # of the command syntax, and thus uninteresting.
        #
        # We stop right before the last entry.

        subgroups = cls.subgroup_patterns
        pattern = open_delimiter
        for i in range(len(subgroups)-1):
            grammer = subgroups[i]
            if grammer is None:
                pattern = pattern + pp.SkipTo(subgroup_delimitor, ignore=ignore_recursion)
            else:
                pattern = pattern + pp.Suppress(pp.Literal(grammer))
            pattern = pattern + pp.Suppress(subgroup_delimitor)
        #We finish the compilation manually.
        #
        # If the last element is none, skip to the ending delimiter.
        # Else, just capture and suppress that element.

        if subgroups[-1] is None:
            pattern = pattern + pp.SkipTo(close_delimiter, ignore=ignore_recursion)
        else:
            pattern = pattern + pp.Suppress(pp.Literal(subgroups[-1]))
        pattern = pattern + close_delimiter
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


    ### Useful functions. The following is designed to be utilized by the subclasses. ###




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
        end_at = 0
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
            directive = cls(token,
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
        if pos < len(original_string):
            unaltered_segment = original_string[pos:len(original_string)]
            output_string += unaltered_segment

        return output_string, directives_dict
    @classmethod
    def reformat(cls, string: str, formatting: Dict[str, str])->str:
        """Go through each dict pair in formatting. Replace key with value"""
        for token, value in formatting.items():
            string = string.replace(token, value)
        return string
    @classmethod
    def compile_directives(self,
               context: Context,
               string: str,
               parser: Callable[[Context,str], str])->Tuple[str, Dict[str, str]]:
        """
        Compiles the directives in a particular incoming string.
        The current context and the parser function must be provided,
        allowing for compilation of subcomponents if desired.

        It is important to note that this only claims, then compiles, the
        individual issued tokens into a dictionary and then returns it. Due
        to order of operations rearing it's head, final assembly occurs
        further along. Conceptually, one can replace the tokens in the primary
        string with the indicated values in the returned dictionary.

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
    subgroup_patterns = (None,)

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
    alias_magic_word= "ALIAS"
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
            _, join_str, repeat_feature, _ = directive.subgroups
            alias_magic_word = cls.token_magic_word + cls.alias_magic_word
            aliased_subcontext, alias = Keyword_Alias.claim_alias(subcontext, alias_magic_word)

            join_str = parser(subcontext, join_str)
            template = parser(aliased_subcontext, repeat_feature)
            keywords = {key : context.keywords[key] for key in alias.find_aliases_in_string(template)}

            #Having done standard parsing, go fetch lists and perform the multifill

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
                list_keywords.update({key : [value]*standard_length for key, value in string_keywords.items()})

                instances = []
                for i in range(standard_length):
                    subformatting = {key : value[i] for key, value in list_keywords.items()}
                    instance = alias.substitute(template, subformatting)
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

    <!!REPLICATEINDENT!!>
    """
    directive_type = "ReplicateIndent"
    token_magic_word= "REPINDENT"
    formatting_select_indicators = ("<!!", "!>>")
    subgroup_patterns = ("REPLICATEINDENT",)

    @classmethod
    def compile_directives(cls,
               context: Context,
               string: str,
               parser: Callable[[Context,str], str]) ->Tuple[str, Dict[str, str]]:

        output_string, directives = cls.get_directives(string)
        original_string = context.source_string
        formatting = {}
        for token, directive in directives.items():
            if context.start_token_loc is None:
                # Handle raw replicate indent. If someone wants to use
                # one for whatever reason???
                endpoint = original_string.index(token)
            else:
                endpoint = context.start_token_loc
            startpoint = original_string.rfind("\n", 0, endpoint)
            if startpoint == -1:
                #Hit start of line
                startpoint = 0
            else:
                #Do not include new line char.
                startpoint += 1
            indent_string = original_string[startpoint:endpoint]
            formatting[token] = indent_string
        return output_string, formatting

class Resolver():
    """
    The resolver has two primary jobs.
    These jobs are to be aware of and
    impliment the order of operations,
    and to perform final assembly
    in the required manner for the
    particular objective.
    """
    # The resolution_sequence
    # list given below indicates what
    # will go off and in what order.
    #
    # Simply adding a new entry to the
    # list will add a new operator.

    resolution_sequence = (
        EscapeDirective,
        FormatMultifill,
        ReplicateIndent,
        Lookup
    )
    @staticmethod
    def get_formatting(directives: Dict[str, Directive])->Dict[str, str]:
        """
        Turns a dictionary of directives into it's formatting equivalent.
        Does this without modification.

        :param directives: A stack of directive
        :return: A formatting dictionary
        """
        formatting = {}
        for token, directive in directives.items():
            formatting[token] = directive.entire_directive
        return formatting

    @classmethod
    def dedent(cls, string: str)->str:
        """
        A context aware dedent function, this will remove
        ugly and unnecessary spaces from a particular
        string of text. It will ignore special characters that
        are defined within commands.

        :param string: The string to dedent
        :return: A dedented string
        """
        token_restore_stack = []
        for DirectiveParser in cls.resolution_sequence:
            if DirectiveParser.string_has_match(string):
                try:
                    string, directives = DirectiveParser.get_directives(string)
                    formatting = cls.get_formatting(directives)
                    token_restore_stack.append(formatting)
                except SubtemplateCompileFailure as err:
                    raise err
        string = textwrap.dedent(string)
        token_restore_stack.reverse()
        for formatting in token_restore_stack:
            string = cls.format(formatting, string)
        return string


    @staticmethod
    def format(formatting_dict: Dict[str, str], string: str)->str:
        """Performs replacement of items given by the formatting dict
        with their corresponding value"""
        for key, value in formatting_dict.items():
            string = string.replace(key, value)
        return string
    @classmethod
    def parse(cls, context: Context, string: str,)->str:
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

        #Parse everything moving forward
        token_restore_stack = []
        for DirectiveParser in cls.resolution_sequence:
            if DirectiveParser.string_has_match(string):
                try:
                    string, formatting = DirectiveParser.compile_directives(context, string, cls.parse)
                    token_restore_stack.append(formatting)
                except SubtemplateCompileFailure as err:
                    raise err

        #Substitute in tokens
        token_restore_stack.reverse()
        for token_formatting in token_restore_stack:
            string = cls.format(token_formatting, string)
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


    def __contains__(self, key: str)->bool:
        """Checks if we contain the indicated feature. Makes template behave something like a list"""
        if not hasattr(self, key):
            return False
        if not isinstance(getattr(self, key), str):
            return False
        return True

    def __getitem__(self, key)->str:
        """Allows for getting subtemplates by name, if they exist"""
        if key not in self:
            raise AttributeError("No subtemplate of name %s attached to class" % key)
        return getattr(self, key)

    def __init__(self, name: str):
        """
        Sets the template up to compile item with
        name
        :param name: The template to compile
        """
        if name not in self:
            raise AttributeError("No template of name %s found among attributes" %name)
        self.__PrimaryTemplate = self[name]
    def __call__(self, keywords: Dict[str, str])->str:
        """Uses keywords to compile the given template, recursively"""
        primary = self.__PrimaryTemplate
        context = Context(keywords, self, primary)
        return Resolver.parse(context, primary)
