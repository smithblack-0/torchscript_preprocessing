"""

A test module for the templates section

Templates contain code which will subsequently
be filled in by program details, in order to
cause various effects.


"""
import unittest
import difflib
from src import templates


#### Base template tests ####
class test_get_formatting_substrings_interactions(unittest.TestCase):

    """
    Test the ability of the get formatting substring
    method to reliably get the chunks within '{}' while
    handling errors.
    """
    def test_get_basic_strings_works(self):
        """Tests if basic selection works"""
        basic_selection_string = "random text{select} more random select {also_select}"
        raw_extracted_results = ['{select}', '{also_select}']
        trimmed_results = ['select', 'also_select']

        _, format_substrings = templates.Template.get_formatting_directives(basic_selection_string)
        self.assertTrue(len(format_substrings) == len(raw_extracted_results))
        for substring, raw, trimmed in zip(format_substrings, raw_extracted_results, trimmed_results):
            self.assertTrue(substring.raw_substring == raw, "Selection did not match")
            self.assertTrue(substring.trimmed_substring == trimmed, "Selection did not match")
    def test_escape_char_works(self):
        """The format escape char for python, using { }, is doubling up as {{ }}. Check this works"""
        escape_string =" This string has an escape. The following should not be noticed {{Do not notice}}"
        expected_escaped_string = " This string has an escape. The following should not be noticed {Do not notice}"
        revised_template, format_substrings = templates.Template.get_formatting_directives(escape_string)
        self.assertTrue(len(format_substrings) == 0, "Did not ignore escape characters")
        self.assertTrue(revised_template==expected_escaped_string)
    def test_nested_strings_work(self):
        """Test if nested escape chars work properly."""
        escape_nested = "This has nested { internal {item { subitem}}}, {item}"
        expected = ["{ internal {item { subitem}}}", "{item}"]
        _, format_substrings = templates.Template.get_formatting_directives(escape_nested)
        for result, expectation in zip(format_substrings, expected):
            self.assertTrue(result.raw_substring==expectation, "Result and expectation do not match")


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


