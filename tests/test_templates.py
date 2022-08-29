"""

A test module for the templates section

Templates contain code which will subsequently
be filled in by program details, in order to
cause various effects.


"""
import unittest
import difflib
import pyparsing as pp
from src import templates



class test_Directive_Base(unittest.TestCase):
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
    def test_get_directives(self):
        """Test the ability of the parser to get directive instances given targets"""
        class Mockup(templates.Directive):
            directive_type = "Mockup"
            select_indicators = ("{", "}")
            token_magic_word = "MOCKUP"
            subgroup_patterns = (None,)

        string = " this should not be matches {this_should_be} this should not be {this_also_should_be}"
        contents = ["this_should_be", "this_should_also_be"]
        tokens = ["<####MOCKUP0####>", "<####MOCKUP1####>"]
        reformatted, directives = Mockup.get_directives(string)
        formatting = {}
        for token, directive in directives:
            self.assertTrue(token in tokens)
            self.assertTrue(directive.content in contents)
            formatting[token] = directive.entire_directive
        restored_string = reformatted.format(**formatting)
        print(restored_string)
        print(string)
        self.assertTrue(restored_string == string)

#### Base template tests ####
class test_DirectiveParser(unittest.TestCase):

    """
    Test the ability of the directive
    parser to perform its job. This consists of

    #Identifying when a directive is in the provided string
    #Extracting and parsing the directive, then returning the result and formatting features
    """


    def test_make_pattern(self):
        pattern = self.Mockup.get_select_pattern()
        string = "this should not be matches {thisshouldbe} this should not be {this_also_should_be}"
        results = ["thisshouldbe", "this_also_should_be"]
        for match in pattern.scan_string(string):
             result = match[0]
             feature = result[1]
             print(feature)
             self.assertTrue(feature in results)






class test_base_Template(unittest.TestCase):
    """
    Test the functionality of the base
    template.

    * Test correct selection of format blocks
    * Test basic format works
        * With keywords
        * With static template
    *Test chained format works
        *With keywords
        * With static templates
    * Test multifill works
        * As aliased template
        * Depending on keywords
    * Test error works reasonably
        * When missing keyword
        * Chains together
        * When insane template.
    """
    def test_get_formatting_substrings(self):
        """
        Test the ability to properly get formatting substrings

        * Test ability to work when dealing with basic cases
        * Test ability to work with nested cases
        * Test too many '{' errors
        * Test too many '}' errors
        """


