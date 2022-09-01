"""

A test module for the templates section

Templates contain code which will subsequently
be filled in by program details, in order to
cause various effects.


"""
import unittest
import difflib
import textwrap
import pyparsing as pp
from src import templates


class TestKit(unittest.TestCase):
    def assert_same_strings(self, string1: str, string2: str):
        """
        Assert two strings are the same.

        If they are not, figure out where, and
        send that information forward to the console.
        """
        if string1 != string2:
            lines_a = string1.splitlines()
            lines_b = string2.splitlines()

            message = "Strings not equal. Detailed comparison: \n"
            for i, (linea, lineb) in enumerate(zip(lines_a, lines_b)):
                submessage = "Line No:" +str(i) + "\n"
                submessage += linea + "\n"
                submessage += lineb + "\n"
                differences = difflib.ndiff(linea, lineb)
                comparison = ""
                for diff in differences:
                    comparison += diff[0]
                submessage += comparison + "\n"
                message += submessage + "\n"
            raise AssertionError(message)


class test_Alias(TestKit):
    """
    Test the keyword alias unit. This
    allows for substitution to be delayed
    until later on.
    """
    def test_claim(self):
        """Test the ability to setup an alias"""
        test_context = templates.Context({"key1" : "potato", "key2" : "tomato"}, {}, "")
        current_keywords = {"key1" : "potato", "key2" : "tomato"}
        expected_keywords = {"key1" : "<$$TEST0$$>", "key2" : "<$$TEST1$$>"}
        context, alias = templates.Keyword_Alias.claim_alias(test_context, "TEST")
        self.assertTrue(expected_keywords == context.keywords)
    def test_identify(self):
        """Test the ability to identify aliases in a string"""
        test_context = templates.Context({"key1" : "potato", "key2" : "tomato"}, {}, "")
        current_keywords = {"key1" : "potato", "key2" : "tomato"}
        context, alias = templates.Keyword_Alias.claim_alias(test_context, "TEST")
        test_string = "item <$$TEST0$$> item "
        expected_result = ["key1"]
        self.assertTrue(expected_result==alias.find_aliases_in_string(test_string))
    def test_substitute(self):
        """Test the ability to substitute in an alias later"""
        test_context = templates.Context({"key1" : "potato", "key2" : "tomato"}, {}, "")
        current_keywords = {"key1" : "potato", "key2" : "tomato"}
        context, alias = templates.Keyword_Alias.claim_alias(test_context, "TEST")
        test_string = "item <$$TEST0$$> item"
        expected_string = "item ham item"
        output = alias.substitute(test_string, {"key1": "ham"})
        self.assert_same_strings(output, expected_string)

class unittest_Directive_Base(TestKit):
    """
    Test the ability of the directive parser to
    make patterns given the class subdefinitions
    """
    def test_get_pattern_basic(self):
        """Test a simple capture definition"""
        class Mockup(templates.Directive):
            directive_type = "Mockup"
            select_indicators = ("{", "}")
            token_magic_word = "MOCKUP"
            subgroup_patterns = (None,)

        string = "Ignore {catch this} {also_this}"
        expectations = ["catch this", "also_this"]
        pattern = Mockup.get_select_pattern()
        for match in pattern.scan_string(string):
            result = match[0]
            _, content, _ = result
            self.assertTrue(content in expectations)
    def test_pattern_syntax_keywords(self):
        """Test generation and fetching of more complex patterns works"""
        class Mockup(templates.Directive):
            directive_type = "Mockup"
            select_indicators = ("<!", "!>")
            token_magic_word = "MOCKUP"
            subgroup_patterns = ("START", None,)

        string = "Ignore <!START|-|This should be captured!> <!This should not be captured!>"
        expectations = ["This should be captured"]
        pattern = Mockup.get_select_pattern()
        for match in pattern.scan_string(string):
            result = match[0]
            _, content, _ = result
            self.assertTrue(content in expectations)
    def test_nested_pattern(self):
        """Test pattern catching works correctly on nested examples"""
        class Mockup(templates.Directive):
            directive_type = "Mockup"
            select_indicators = ("<!", "!>")
            token_magic_word = "MOCKUP"
            subgroup_patterns = ("START", None,)

        string = "Ignore <!START|=|<!This should be captured<!deeper!>!> !> <!This should not be captured!>"
        expectations = ["<!This should be captured<!deeper!>!> "]
        pattern = Mockup.get_select_pattern()
        matches = list(pattern.scan_string(string))
        self.assertTrue(len(expectations) == len(matches))
        for match in pattern.scan_string(string):
            result = match[0]
            _, content, _ = result
            self.assertTrue(content in expectations)
    def test_string_has_match(self):
        """Test that has match is functioning correctly."""
        class Mockup(templates.Directive):
            directive_type = "Mockup"
            select_indicators = ("{", "}")
            token_magic_word = "MOCKUP"
            subgroup_patterns = (None,)

        string_with_match = " {test} "
        string_no_match = " this has no match"
        string_multi_match = "test {test} {test2}"

        self.assertTrue(Mockup.string_has_match(string_with_match))
        self.assertTrue(Mockup.string_has_match(string_multi_match))
        self.assertFalse(Mockup.string_has_match(string_no_match))
    def test_get_directives(self):
        """Test the ability of the parser to get directive instances given targets"""
        class Mockup(templates.Directive):
            directive_type = "Mockup"
            select_indicators = ("{", "}")
            token_magic_word = "MOCKUP"

            subgroup_patterns = (None,)

        string = "this should not be matches {this_should_be} this should not be {this_also_should_be} post"
        expected_output = "this should not be matches <####MOCKUP0####> this should not be <####MOCKUP1####> post"
        reformatted, directives = Mockup.get_directives(string)
        self.assert_same_strings(expected_output, reformatted)

        contents = ["this_should_be", "this_also_should_be"]
        formatting = {}
        for token, directive in directives.items():
            self.assertTrue(directive.content in contents)
            formatting[token] = directive.entire_directive
        restored_string = reformatted
        for token, replace in formatting.items():
            restored_string = restored_string.replace(token, replace)
        self.assertTrue(restored_string == string)\



class unittest_Directive_Subclasses(TestKit):
    """
    Tests that the subclasses of the directive
    parser are functioning the way they should.
    """
    def test_lookup(self):
        """Test that the keyword directive system is correctly tracking down keywords when needed"""

        def parser_mockup(context, string):
            return string

        test_string = "{keyword} No keyword {template}"
        context = templates.Context({"keyword" : "potato"}, {"template" : "tomato"}, test_string)
        output_string, formatting_dict = templates.Lookup.compile_directives(context, test_string, parser_mockup)
        final_string = templates.Resolver.format(formatting_dict, output_string)
        self.assertTrue("potato" in final_string)
        self.assertTrue("tomato" in final_string)


        test_raise = "{neither}"
        def tester():
            output_string, formatting_dict = templates.Lookup.compile_directives(context, test_raise, parser_mockup)
        self.assertRaises(templates.TemplateKeyNotFound, tester)
    def test_escape(self):
        """Tests the escape template ability"""
        def parser_mockup(context, string):
            return string

        test_string = "{do_not_escape} stuff {{do_escape}}"
        expected_string = "{do_not_escape} stuff {do_escape}"
        context = templates.Context({},{}, test_string)
        output_string, formatting_dict = templates.EscapeDirective.compile_directives(context, test_string, parser_mockup)
        output_string = templates.Resolver.format(formatting_dict, output_string)
    def test_format_multifill(self):
        """Test that the format multifill works when sitting by itself"""

        def parser_mockup(context, string: str)->str:
            return templates.Resolver.parse(context, string)

        people_a = ["Bob", "Jessy", "Eric"]
        people_b = ["George", "Harold", "Chris"]
        boss = "Bill"

        test_string = "prior <!!MULTIFILL|=|, |=|{people_a} works with {people_b} under {boss}!!> post"
        expected_result = "prior Bob works with George under Bill, Jessy works with Harold under Bill, Eric works with Chris under Bill post"
        context = templates.Context({"people_a" : people_a, "people_b" : people_b, "boss" : boss},
                                    {}, test_string)

        output_string, formatting_dict = templates.FormatMultifill.compile_directives(context, test_string, parser_mockup)
        output_string = templates.Resolver.format(formatting_dict, output_string)
        self.assert_same_strings(output_string, expected_result)
    def test_ReplicateIndent_top_level(self):
        """Test replicate indent. This should, unsuprisingly, replicate an indent."""
        def parser_mockup(context, string: str)->str:
            return string


        test_string ="""
        do nothing stuff
              <!!REPLICATEINDENT!!>post
        aaaaaa<!!REPLICATEINDENT!!>post
        """
        expected_result ="""
        do nothing stuff
                    post
        aaaaaaaaaaaapost
        """

        test_string = textwrap.dedent(test_string)
        expected_result = textwrap.dedent(expected_result)

        context = templates.Context({}, {},test_string)
        output_string, formatting = templates.ReplicateIndent.compile_directives(context, test_string, parser_mockup )
        output_string = templates.Resolver.format(formatting, output_string)
        self.assert_same_strings(output_string, expected_result)
    def test_ReplicateIndent_restricted(self):
        """Test that replicate indent will go ahead and work properly when a region is restricted"""
        def parser_mockup(context, string: str)->str:
            return string


        test_string = """\
        unrestricted<<Restricted <!!REPLICATEINDENT!!> >>
        """
        expected_string = """\
        unrestricted<<Restricted unrestricted >>
        """
        test_string = textwrap.dedent(test_string)
        expected_string = textwrap.dedent(expected_string)

        start_restricted = test_string.index("<<Restricted")
        end_restricted = test_string.index(">>") + 1
        context = templates.Context({}, {}, test_string,
                                    start_token_loc=start_restricted,
                                    end_token_loc=end_restricted)
        output_string, formatting = templates.ReplicateIndent.compile_directives(context, test_string, parser_mockup )
        output_string = templates.Resolver.format(formatting, output_string)
        self.assert_same_strings(output_string, expected_string)

class unittest_Parser(TestKit):
    """
    Test the parser and formatting functions
    """
    def test_parse(self):
        test_string = textwrap.dedent("""
        this is a {keyword}
        this is an {{escape {keyword}}}
        this is a {template} feature
        shouldduplicate<!!REPLICATEINDENT!!>
        """)
        expectation_string = textwrap.dedent("""
        this is a apple
        this is an {escape {keyword}}
        this is a banana feature
        shouldduplicateshouldduplicate
        """)


        keywords = {"keyword" : "apple"}
        template_mockup = {"template" : "banana"}
        context = templates.Context(keywords,
                                    template_mockup,
                                    test_string)
        output = templates.Resolver.parse(context, test_string)


        try:
            self.assert_same_strings(output, expectation_string)
        except AssertionError as err:
            raise err

class integration_test_Template(TestKit):
    """
    Tests the entire core templating system by
    putting the various pieces together into a single
    example.
    """
    def test_basic_template(self):
        class mockup_template(templates.Template):
            primary = templates.Resolver.dedent(
                """
                This is the primary template output
                
                The following is a keyword, and should be replaced: {keyword}
                The following is a multifill, and should be replaced: <!!MULTIFILL|=|WWW|=|{items}!!>
                The following is a template lookup {template}
                The following is a captured multifill:
                    <!!MULTIFILL|=|<!!REPLICATEINDENT!!>|=|{items}\n!!>"""
            )
            template = "This is just an additional keyword puzzle: {keyword2}"

        expectations = templates.Resolver.dedent(
            """
            This is the primary template output
    
            The following is a keyword, and should be replaced: apple
            The following is a multifill, and should be replaced: AWWWBWWWC
            The following is a template lookup This is just an additional keyword puzzle: grape
            The following is a captured multifill:
                A
                B
                C
            """
        )

        instance = mockup_template("primary")
        keywords = {"keyword" : "apple", "keyword2" : "grape"}
        keywords["items"] = ["A", "B", "C"]
        output = instance(keywords)
        self.assert_same_strings(output, expectations)