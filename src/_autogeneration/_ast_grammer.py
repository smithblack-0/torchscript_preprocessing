import _ast as ast
import string
import textwrap
import re
import sys
from packaging import version
from dataclasses import dataclass
from typing import List, Union, Dict, Optional, Type, Generator

test = open("_ast_grammer/ast_grammer_python_v3.8.txt", "r").read()


#Get correct ast vocabulary
version_data = sys.version_info
current_version = version.parse("{major}.{minor}.{micro}".format(major=version_data.major,
                                                                 minor = version_data.minor,
                                                                 micro = version_data.micro))
if current_version < version.parse("3.5"):
    raise NotImplementedError("Version too old")
    grammer = open("_ast_grammer/ast_grammer_python_v2.7.txt").read()
elif current_version < version.parse("3.6"):
    grammer = open("_ast_grammer/ast_grammer_python_v3.5.txt").read()
elif current_version < version.parse("3.7"):
    grammer = open("_ast_grammer/ast_grammer_python_v3.6.txt").read()
elif current_version < version.parse('3.8'):
    grammer = open("_ast_grammer/ast_grammer_python_v3.7.txt").read()
elif current_version < version.parse("3.9"):
    grammer = open("_ast_grammer/ast_grammer_python_v3.8.txt").read()
elif current_version < version.parse("3.10"):
    grammer = open("_ast_grammer/ast_grammer_python_v3.9.txt").read()
else:
    grammer = open("_ast_grammer/ast_grammer_python_v3.10.txt").read()
grammer = re.search(r"{[\S\s]+}", grammer).group().strip("{").strip("}").strip("\n")




literal_map = {'identifier' : (str, "str"),
               'constant' : (Union[str, int, float, complex, bool, None], "Union[str, int, float, complex, bool, None]"),
               'string' : (str, "str"),
               'int' : (int, "int")
               }

@dataclass
class signature_node:
    """Represents one item in a signature"""
    name: str
    type_str: str
    type: Type
    list: bool = False
    optional: bool = False

@dataclass
class subchild:
    """Represents a subchild of an ast feature"""
    name: str
    ast_typing: Type[ast.AST]
    arguments: List[signature_node]
    def lookup(self, argument: str)->signature_node:
        for arg in self.arguments:
            if arg.name == argument:
                return arg
@dataclass
class syntax_group:
    """Represents a top level ast group"""
    name: str
    ast_typing: Type[ast.AST]
    subclasses: List[subchild]
    attributes: Optional[List[signature_node]] = None
    arguments: None = None
    def iter(self)->Generator[Union[subchild, "syntax_group"], None, None]:
        """Iterates over nodes in this group"""
        yield self
        for subchild in self.subclasses:
            yield subchild
    def lookup(self, name: str)->Union[subchild, "syntax_group"]:
        if self.name == name:
            return self
        for subchild in self.subclasses:
            if subchild.name == name:
                return subchild

@dataclass
class syntax_tree:
    """Represents the entire syntax tree"""
    groups: List[syntax_group]
    def iter(self)->Generator[Union[subchild, "syntax_group"], None, None]:
        """Iterates over every node in the tree"""
        for group in self.groups:
            for child in group.iter():
                yield child
    def lookup(self, name: str)->subchild:
        for group in self.groups:
            if group.lookup(name) is not None:
                return group.lookup(name)

def get_syntax_groups(grammer: str)->List[str]:
    """
    Splits the grammer into syntax groups
    by detecting where characters immediately
    follow new lines

    :return: List[str]
    """
    grammer = textwrap.dedent(grammer)
    lines = grammer.splitlines()
    groups = []
    startslice = 0
    endslice = 0
    for line in lines:
        if len(line) > 0 and line[0] in string.ascii_letters:
            #This is a root of a group
            groups.append(grammer[startslice:endslice])
            startslice = endslice
        endslice += len(line) + 1 #The plus one is for the new line char
    return groups

def get_signature_node(details: str)->signature_node:
    """Create a signature node from the details string"""
    is_list = False
    is_optional = False
    pieces = re.split(r" +", details)
    typehint, argname = pieces

    # Handle special varietations
    if typehint.endswith("*"):
        is_list = True
        typehint = typehint.strip("*")
    if typehint.endswith("?"):
        is_optional = True
        typehint = typehint.strip("?")
    if argname.startswith("*"):
        is_list = True
        argname = argname.strip("*")
    if argname.startswith("?"):
        is_optional = True
        argname = argname.strip("?")

    # Fetch typing info
    if hasattr(ast, typehint):
        arg_typing = getattr(ast, typehint)
        arg_typestring = "ast." + arg_typing.__name__
    else:
        arg_typing, arg_typestring = literal_map[typehint]
    if is_list:
        arg_typestring = "List[{}]".format(arg_typestring)
    if is_optional:
        arg_typestring = "Optional[{}]".format(arg_typestring)

    # Make and return node
    signode = signature_node(argname, arg_typestring, arg_typing, is_list, is_optional)
    return signode

def get_subchild(subchild_grammer: str)->subchild:
    """Create a subchild from an isolated syntax string"""
    if "(" in subchild_grammer and ")" in subchild_grammer:
        #Arguments exist. We must now construct them
        name, args = subchild_grammer.split("(")
        args = args.rstrip(")")
        args = [item.strip() for item in args.split(",")]
        finished_arguments = []
        for arg in args:
            signode = get_signature_node(arg)
            finished_arguments.append(signode)
    else:
        #No arguments exist. Simply generate name, and indicate state
        name = subchild_grammer.strip()
        finished_arguments = None
    ast_typing = getattr(ast, name)
    return subchild(name, ast_typing, finished_arguments)

def get_syntactic_tree(grammer: str):
    """
    Gets the syntactic support tree from the
    source documentation

    :param grammer: The grammer definitions
    :return: The syntactic tree.
    """
    groups = get_syntax_groups(grammer)
    output_groups = []
    for group in groups:
        if "=" not in group:
            #Skips blank strings at the start, or anything else which is not formatted right.
            continue

        #Fetch syntax group name and content.
        name, subclasses = group.split("=")
        name = name.strip().strip("\n")
        if not hasattr(ast, name):
            #TODO: revise
            #This is a fix for the fact match is not in python 3.9
            continue

        print("collecting data on primary class", name)
        subclasses = subclasses.strip().strip("\n\n") #Strip end chars
        subclasses = re.sub(r"--.*", "", subclasses) #Strip comments out of file
        attributes = re.search("attributes.*", subclasses)
        if attributes is not None:
            #Build an attribute file, if needed.
            attributes = attributes.group()
            assert "|" not in attributes, "Grammer requires massaging"
            subclasses = re.sub("attributes.*", "", subclasses)

            #Build nodes
            _, args = attributes.split("(")
            args = args.strip(")")
            args = [item.strip() for item in args.split(",")]
            final_attributes = []
            for arg in args:
                node = get_signature_node(arg)
                final_attributes.append(node)
            attributes = final_attributes

        subclasses = [item.strip() for item in subclasses.split("|")]
        output_classes = []
        for subclass in subclasses:
            print("collecting data on", name, "subclass", subclass)
            if subclass.startswith("("):
                #This does a little rewriting, such that, for example,
                #   comprehension = (expr target, expr iter, expr* ifs, int is_async)
                # will instead be seen as
                #   comprehension = comprehension(expr target, expr iter, expr* ifs, int is_async)
                print('lazy documentation detected')
                subclass = name + subclass
                print("now collecting data on", name, "subclass", subclass)


            if "(" in subclass:
                endpoint = subclass.index("(")
                subclassname = subclass[:endpoint]
            else:
                subclassname = subclass
            if not hasattr(ast, subclassname):
                continue
            output_classes.append(get_subchild(subclass))
        node = syntax_group(name, getattr(ast, name), output_classes, attributes)
        output_groups.append(node)
    return syntax_tree(output_groups)

grammer_tree = get_syntactic_tree(grammer)




