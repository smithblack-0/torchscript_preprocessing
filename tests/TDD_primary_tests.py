"""
This is a collection of tests used
to drive the test driven development
paradyn.

It includes expectations for classes,
functions, and inline text.
"""
from typing import Type, List, Any, Callable, Union
import unittest
import inspect
import textwrap
import difflib



def run_rewrite(item, recursive_depth: int = 5)->Type:
    raise NotImplementedError()
def get_source(cls: Type)->str:
    source = inspect.getsource(cls)
    source = textwrap.dedent(source)
    return source


#Notes:
#


class testUtils(unittest.TestCase):
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
    def util_test_issubclass(self, totest: Type, Bases: List[Type]):
        for base in Bases:
            self.assertTrue(issubclass(totest, base))
    def util_test_isinstance(self, totest: Any, Bases: List[Type]):
        """Tests that the test item is a base for all bases"""
        for base in Bases:
            self.assertTrue(isinstance(totest, base))


class testInheritanceStatic(testUtils):
    """
    Test fixture for testing inheritance preprocess under static
    conditions. Targets methods which have no parameters,
    and which follow the MRO chain. Follows said chain,
    and yields result which looks and sees if results
    line up with the correct python code implimentation.

    * Test static inheritance
    * Test static logic
    * Test isinstance
    * Test issubclass
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
        Final = run_rewrite(Inheritor)
        self.util_test_issubclass(Final, [Inheritor, Base])
        instance = Final()
        original_instance = Inheritor()
        self.util_test_isinstance(instance, [Inheritor, Base])
        self.assertTrue(instance.method_to_override() == original_instance.method_to_override())
        self.assertTrue(instance.method_to_inherit() == original_instance.method_to_inherit())

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

        #Test OOP
        Final = run_rewrite(Inheritor)
        self.util_test_issubclass(Final, [Inheritor, Complication, Base])
        instance = Final()
        original_instance = Inheritor()
        self.util_test_isinstance(instance, [Inheritor, Complication, Base])

        #Test logic

        self.assertTrue(instance.method_to_override() == original_instance.method_to_override())
        self.assertTrue(instance.method_to_inherit() == original_instance.method_to_inherit())
        self.assertTrue(instance.method_to_inherit_2() == original_instance.method_to_inherit_2())

    def test_inheritance_multiple(self):
        """
        Tests that multiple inheritance is being
        rewritten correctly. Ensures that
        MRO chain is being followed. Static analysis only,
        which makes it easier in some ways.

        The hardest test in this suite
        """
        class Subbase():
            def method_to_be_subinherited(self):
                return 0

        #Starting state
        class Base1(Subbase):
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

        #Test OOP logic.
        First = run_rewrite(Subbase)
        Final = run_rewrite(Inheritor)
        self.util_test_issubclass(Final, [Base2, Base1, Subbase, First])
        instance = Final()
        original_instance = Inheritor()
        self.util_test_isinstance(instance, [Base1, Base2, Subbase, First])


        #Test Logic

        self.assertTrue(instance.method_to_override_final() == original_instance.method_to_override_final())
        self.assertTrue(instance.method_to_override_intermediate() == original_instance.method_to_override_intermediate())
        self.assertTrue(instance.method_that_should_not_be_overridden() == original_instance.method_that_should_not_be_overridden())
        self.assertTrue(instance.method_to_be_inherited() == original_instance.method_to_be_inherited())
        self.assertTrue(instance.method_to_be_inherited_2() == original_instance.method_to_be_inherited_2())
        self.assertTrue(instance.method_to_be_subinherited() == original_instance.method_to_be_subinherited())


class testClassAttributes(testUtils):
    """
    Test the ability of the logic to properly
    setup a class attribute as a wrapper entity backed
    by a databank. Test it under inheritance. Test the
    storage backend is being generated correctly, and
    access works.

    * Test class attribute wrapper packet creation
    * Test wrapper packet transparently redirects on issubclass and isinstance
    * Test that attributes are now properly accessible from instance
    * Test that attributes are properly accessable from class
    * Test chained inheritance works properly.
    """
    def test_class_attribute_access(self):
        """A basic test of the attributes system
        * Can we make mutable class attributes.
        * Does the class method wrapper work correctly
        * Do they sync across instances
        * Do they respond to isinstance and issubclass properly?
        * Do class methods work properly?
        """
        class ClassAttributesTester():
            item = 3
            item2 = [5]
            @classmethod
            def append(cls, value: int):
                cls.item2.append(value)
            def __init__(self, paremeter: int):
                self.paremeter = paremeter

        Final = run_rewrite(ClassAttributesTester)

        #Test class level access is functional
        self.assertTrue(ClassAttributesTester.item == Final.item)
        Final.append(3)
        self.assertTrue(ClassAttributesTester.item2[1] == Final.item2[1])
        self.util_test_issubclass(Final, [ClassAttributesTester, Final])

        instance_one_a = Final(3)
        instance_two_a = Final(4)

        self.util_test_isinstance(instance_one_a, [ClassAttributesTester, Final])

        instance_one_a.append(2)

        self.assertTrue(instance_two_a.item2[2] == instance_one_a.item2[2])
    def test_class_attribute_inheritance(self):
        """
        Test class attributes function correctly when
        undergoing an inheritance process.

        * Are classmethods inheriting properly
        * Are class fields inheriting properly
        * Are changes to class fields propogating through the inheritance chain.
        """
        class ClassAttributeBase():
            registry = [1, 2, 3]
            @classmethod
            def modify_registry(cls, value: int):
                cls.registry.append(value)


        class ClassAttributesTester(ClassAttributeBase):
            item = 3
            item2 = [5]

            @classmethod
            def append(cls, value: int):
                cls.item2.append(value)

            def __init__(self, paremeter: int):
                self.paremeter = paremeter

        Intermediate = run_rewrite(ClassAttributeBase)
        Final = run_rewrite(ClassAttributesTester)

        self.util_test_issubclass(Final, [ClassAttributesTester, ClassAttributeBase, Intermediate])
        self.Final.modify_registry(6)
        self.assertTrue(Final.registry[-1] == Intermediate.registry[-1])


class testInlineRewriting(testUtils):
    """
    Test the ability of the preprocessor
    to properly handle inline definition of
    classes and functions.

    * Test inline function defitition and return is supported
    * Test inline class defitition and return is supported
    * Test under basic, nested conditions.
    * Test pass function rewriting
    """

    def test_inline_nested_function(self):
        """ Test that an inline function may be defined and a wrapper is built which will then work"""
        closure = 3
        def inline():
            item = closure
            def internal1():
                def internal2():
                    return item
                return internal2
            return internal1

        Wrapper = run_rewrite(inline)
        internal1 = Wrapper()
        internal2 = internal1()
        item = internal2()
        self.assertTrue(item == closure)
    def test_inline_nested_duel(self):
        """Test if a nested sequence of classes and functions will compile and execute correctly"""
        closure = 1
        closure_parem  = 3
        instance_param = 6
        def inline():
            def deeper():
                class nested():
                    def __init__(self, feature: int):
                        self.feature = feature
                        self.param = closure_parem
                return nested
            return deeper

        Wrapper = run_rewrite(inline)
        deeper = Wrapper()
        nested = deeper()
        instance = nested(instance_param)
        self.assertTrue(instance.feature == instance_param)
        self.assertTrue(instance.param == closure_parem)
    def test_pass_by_function(self):
        """
        Tests the ability of the preprocessor to track
        down the expected type in order to pass in
        a constructed function

        * Should track down and couple based on input specifications.
        """
        def a()->int:
            return 3
        def b()->int:
            return 4
        def c()->str:
            return "5"
        def process(func: Union[a,b,c])->Union[int, str]:
            return func()

        # Test logic
        a_wrapped = run_rewrite(a)
        b_wrapped = run_rewrite(b)
        c_wrapped = run_rewrite(c)
        process_wrapped = run_rewrite(process)

        self.assertTrue(process_wrapped(a) == 3)
        self.assertTrue(process_wrapped(a_wrapped)==3)
        self.assertTrue(process_wrapped(b) == 4)
        self.assertTrue(process_wrapped(b_wrapped) == 4)
        self.assertTrue(process_wrapped(c) == "5")
        self.assertTrue(process_wrapped(c_wrapped) == "5")

class testFunctionRecursiveRewriting(testUtils):
    """
    Test the ability of the preprocessor to
    rewrite recursion.
    """
    def test_tail_optimization(self):
        """Test the ability to handle tail recursion, in which everything
         interesting has happened by the time recursion is reached and
         no stack must be maintained"""

        def tail_call_add_to_five(num: int = 0)->int:
            if num == 5:
                return num
            return tail_call_add_to_five(num+1)

        def colletz_a(number: int)->int:
            if number == 1:
                return number
            else:
                if number % 2 == 0:
                    number = number // 2
                else:
                    number = 3*number + 1
                return colletz_a(number)

        def colletz_b(number: int)->int:
            if number == 1:
                return number
            elif number % 2 == 0:
                return colletz_b(number//2)
            else:
                return colletz_b(3*number + 1)


        tail_wrapper = run_rewrite(tail_call_add_to_five)
        colletz_a_wrapper = run_rewrite(colletz_a)
        colletz_b_wrapper = run_rewrite(colletz_b)

        self.assertTrue(tail_wrapper() == 5)
        self.assertTrue(colletz_a_wrapper(10) == 1)
        self.assertTrue(colletz_b_wrapper(10) == 1)
    def test_static_nested_definition(self):
        """ Test the ability to properly detect and handle a static nested recursion loop."""
        def colletz(number: int)->int:
            def process_number(number: int)->int:
                if number == 1:
                    return number
                if number % 2 == 0:
                    return colletz(number // 2)
                else:
                    return colletz(3*number + 1)
            return process_number(number)
        colletz_wrapper = run_rewrite(colletz)
        self.assertTrue(colletz_wrapper(10) == 1)