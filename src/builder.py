from typing import Optional, Dict, List
from string import Template
from dataclasses import dataclass
import astroid

class_feature_prefix = "__class_feature" #A prefix that goes in front of nodes



class ImmediateClassAnalysis:
    """
    Analyzes class properties without regard
    to children.
    """
    @property
    def class_methods(self)->List[astroid.FunctionDef]:
        output = []
        for item in self.node.body:
            item: astroid.NodeNG = item
            if not isinstance(item, astroid.FunctionDef):
                continue
            if not (item.is_method() and item.is_bound()):
                continue
            #Todo: Figure out how to avoid using a magic string named classmethod. Can we look up it's environmental name?
            if "classmethod" not in item.decoratornames:
                continue
            output.append(item)
        return output
    @property
    def staticmethods(self)->List[astroid.FunctionDef]:
        output = []
        for item in self.node.body:
            item: astroid.NodeNG = item
            if not isinstance(item, astroid.FunctionDef):
                continue
            if not (item.is_method() and item.is_bound()):
                continue
            #Todo: Figure out how to avoid using a magic string named staticmethod. Can we look up it's environmental name?
            if "staticmethod" not in item.decoratornames:
                continue
            output.append(item)
        return output
    @property
    def instance_methods(self)->List[astroid.FunctionDef]:
        output = []
        for item in self.node.body:
            item: astroid.NodeNG = item
            if not isinstance(item, astroid.FunctionDef):
                continue
            if not (item.is_method() and item.is_bound()):
                continue
            #Todo: Figure out how to avoid using a magic string named classmethod. Can we look up it's environmental name?
            if "classmethod" in item.decoratornames:
                continue
            output.append(item)
        return output

    def __init__(self, node: astroid.ClassDef):
        self.node = node

class ClassBuilder():
    """
    Utilized to build classes.
    """

class Builder():
    """
    A top level builder.

    """


    def get_class_binding