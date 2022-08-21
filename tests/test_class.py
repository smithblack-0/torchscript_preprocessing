"""
This is a collection of intial python files
and final rewritten files to keep myself oriented.

Objectives:

Build cases for:

* Single, Multiple, Chained inheritance
* No, instance fields, class fields.
* No, instance super calls, class super calls.
* No, parent instance, parent class field access.
* No, instance functions inherited, class function inherited

"""
from typing import Type
import unittest
import inspect
import textwrap
import difflib


def run_rewrite(cls: Type)->Type:
    raise NotImplementedError()
def get_source(cls: Type)->str:
    source = inspect.getsource(cls)
    source = textwrap.dedent(source)
    return source

class testUtils():
    """Different common test utilities"""

    Differ = difflib.Differ()
    def compare_source(self, source1: str, source2: str):
        """Compare source lines together. Provides some details on what is wrong if error occurs."""
        differences = list(self.Differ.compare(source1, source2))
        for i, difference in enumerate(differences):
            section = source1[min(i-10, 0):max(i+10, len(differences))]
            verdict = True if difference == " " else False
            message = "Source code did not match. At char %s. \n: %s" % (i, section)
            self.assertTrue(verdict, message)


class testInheritanceStatic(unittest.TestCase, testUtils):
    """
    Test fixture for testing inheritance
    rewriting with regards to single, chained and multiple
    inheritance. Class features are not implimented,

    This uses self, but everything is actually static.
    The purpose is just to ensure the program is
    following the MRO right.
    """

    def test_inheritance_single(self):
        """Test that static inheritance is properly functioning
            with a single inheritance cycle"""
        #Startpoint
        class Base:
            def method_to_override(self) -> int:
                return 3
            def method_to_inherit(self) -> int:
                return 4
        class Inheritor(Base):
            def method_to_override(self) -> int:
                return 6
            def __init__(self):
                pass
        original = Inheritor
        #Expected
        class Inheritor:
            def method_to_override(self) -> int:
                return 6
            def __init__(self):
                pass
            def method_to_inherit(self) -> int:
                return 4
        required_source = get_source(Inheritor)
        actual_source = get_source(run_rewrite(original))
        self.compare_source(required_source, actual_source)
    def test_inheritance_chained(self):
        """
        Tests that inheritance will function correctly when chaining
        multiple subclasses together. Tests all functions are correctly captured.
        """
        #Startpoint
        class Base:
            def method_to_override(self) -> int:
                return 3
            def method_to_inherit(self) -> int:
                return 4
        class Complication(Base):
            def method_to_inherit_2(self)->int:
                return 7
            def method_to_override(self)->int:
                return 2
        class Inheritor(Complication):
            def method_to_override(self)->int:
                return 9
            def __init__(self):
                pass
        original = Inheritor
        #Expected endpoint.
        #Methods are appended in the same order as
        #the MRO chain.
        class Inheritor(Complication):
            def method_to_override(self)->int:
                return 9
            def __init__(self):
                pass
            def method_to_inherit_2(self)->int:
                return 7
            def method_to_inherit(self)->int:
                return 4

        required_source = get_source(Inheritor)
        actual_source = get_source(run_rewrite(original))
        self.compare_source(required_source, actual_source)
    def test_inheritance_multiple(self):
        """
        Tests that multiple inheritance is being
        rewritten correctly. Ensures that
        MRO chain is being followed. Static analysis only,
        which makes it easier in some ways.
        """
        #Starting state
        class Base1():
            def method_to_be_inherited(self):
                return 4
            def method_to_override_final(self):
                return 0
            def method_to_override_intermediate(self):
                return 0
            def method_that_should_not_be_overridden(self):
                return 1

        class Base2:
            def method_to_override_intermediate(self):
                return 1
            def method_that_should_not_be_overridden(self):
                return 0
            def method_to_be_inherited_2(self):
                return 4

        class Inheritor(Base2, Base1):
            def method_to_override_final(self):
                return 1
            def __init__(self):
                pass
        original = Inheritor

        #Final
        class Inheritor:
            def method_to_override_final(self):
                return 1
            def __init__(self):
                pass
            def method_to_override_intermediate(self):
                return 1
            def method_that_should_not_be_overridden(self):
                return 0
            def method_to_be_inherited_2(self):
                return 4
            def method_to_be_inherited(self):
                return 4

        required_source = get_source(Inheritor)
        actual_source = get_source(run_rewrite(original))
        self.compare_source(required_source, actual_source)

class testAttributeRewriting(unittest.TestCase, testUtils):
    """
    Tests the ability to store and load attributes
    through parameters as needed by way of rewriting.

    This includes class and methods attributes as
    well as access points.
    """
    def test_instance_attributes(self):
        """Tests that nothing happens when dealing with instance attributes"""
        class Item:
            def __init__(self, thing: int):
                self.item =3
                self.thing = thing
        expected = get_source(Item)
        actual = get_source(run_rewrite(Item))
        self.compare_source(expected, actual)
    def test_class_attributes(self):
