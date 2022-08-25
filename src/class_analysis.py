from typing import Any, List, Optional

import astroid
from dataclasses import dataclass

### Define data classes. These are focused on providing the information
### needed to make decisions on what to do.

NodeType = astroid.NodeNG
ClassType = astroid.ClassDef


@dataclass
class method_analysis:
    name: str
    type_str: str
    node: NodeType

@dataclass
class properties_analysis:
    """An analysis for a property, which can be used for reconstruction"""
    name: str
    getter: NodeType
    node: NodeType
    setter: Optional[NodeType] = None
    deleter: Optional[NodeType] = None

@dataclass
class fields_analysis:
    """ A analysis file for context with the fields. """
    name: str
    node: Any

@dataclass
class instance_analysis:
    """An analysis for the instance attributes.
    Can be used for construction"""
    properties: List[properties_analysis]
    methods: List[method_analysis]
    fields: List[fields_analysis]

@dataclass
class class_analysis:
    """An analysis for the class attributes. Can be used for reconstruction"""
    methods: List[method_analysis]
    fields: List[fields_analysis]

@dataclass
class inheritance_analysis:
    """An analysis for the inheritance attributes"""
    bases: List[ClassType]
    metaclass: Optional[ClassType] = None




class mro_analysis():
    """
    Compiles, then emits,
    code which helps with the
    MRO analysis process.

    This will consist of

    """

def get_class_analysis(node: ClassType, constructor):
        """
        Gets the immediately relevant instance attributes.
        Does not know or care
        """

        if node in constructor.has_node(node):
            return constructor.get_node(node)


        #Get all methods.
        #Get all fields





        methods = node.methods()

        bases = node.bases
        metaclass = node.metaclass






def get_instance_analysis()




class abstract_builder()



class static_instance_mro_analysis():
    """
    Represents the static mro instance analysis
    of a particular class node.

    * Tracks down particulars of
    """


class static_init_mro_analysis():
    """
    Represents a particular static analysis for
    an init in a given program.
    * Tracks down assignment parameters

    """


def get_mro_class_features():
    """
    Get, in order from a class node, the
    method resolution order nodes making
    up the class features portion of the tree,
    along with a bit of their ordering
    :return:
    """



def build_class_feature():
    """
    Builds the astroid definition of a class_feature
    based on the current node and prior class_feature
    nodes.
    :return:
    """