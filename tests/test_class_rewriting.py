from typing import Type
import unittest


def rewrite(object: Type)->Type:
    pass

def is_same(object_1, object_2):
    pass




class Example():
    """
    A base case for an example.

    Tracks subclassed examples for convience
    """
    single_inheritance = False
    multiple_inheritance = False
    chained_inheritance = False

    super_calls = False

    instance_fields = False
    instance_calls = False

    class_fields = False
    class_calls = False

    registry = []

    def __init_subclass__(cls):
        cls.registry.append(cls)

    def get_original(self) -> Type:
        raise NotImplementedError()

    def get_final(self) -> Type:
        raise NotImplementedError()

    def test_run(self):
        original = self.get_original()
        predicted = self.get_final()
        actual = rewrite(original)
        self.assertTrue(predicted, actual)

class NoopExample(Example, unittest.TestCase):
    """ A noop. Nothing happens."""

    def get_original(self) -> Type:
        class Instance():
            def __init__(self):
                print(3)

        return Instance

    def get_final(self) -> Type:
        class Instance():
            def __init__(self):
                print(3)

        return Instance

class testInheritance():
    """


    """


class SimpleSingleInheritanceFixtures(Example, unittest.TestCase):
    """Test single inheritance with instance calls"""
    single_inheritance = True
    instance_calls = True
    def get_original(self) -> Type:


        return Inheritor
    def get_final(self) -> Type:
        class Inheritor():
            def method_to_override(self) -> int:
                return 6
            def __init__(self):
                pass
            def method_to_inherit(self) -> int:
                return 4
        return Inheritor


class SimpleInstanceAttribute(Example):
    """Checks that instance attributes access functions correctly"""
    instance_calls = True
    instance_fields = True

    def get_original(self) -> Type:
        class Item():
            def __init__(self):
                self.item = 4

            def method_to_return_from(self) -> int:
                return self.item

        return Item

    def get_final(self) -> Type:
        class Item():
            def __init__(self):
                self.item = 4

            def method_to_return_from(self) -> int:
                return self.item

        return Item


class SimpleClassAttribute(Example):
    instance_calls = True
    instance_fields = True
    class_fields = True