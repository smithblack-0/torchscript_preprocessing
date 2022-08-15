import ast
import string
import textwrap
import re
from dataclasses import dataclass
from typing import List, Union, Dict, Optional, Type
grammer = open("_ast_grammer_text.txt").read()
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
    ast_feature: Optional[ast.AST]
    subclasses: List[subchild]
    def lookup(self, name: str)->subchild:
        for subchild in self.subclasses:
            if subchild.name == name:
                return subchild


@dataclass
class syntax_tree:
    """Represents the entire syntax tree"""
    groups: List[syntax_group]
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

def get_subchild(subchild_grammer: str)->subchild:
    """Create a subchild from an isolated syntax string"""
    if "(" in subchild_grammer and ")" in subchild_grammer:
        print("trying", subchild_grammer)
        #Arguments exist. We must now construct them
        name, args = subchild_grammer.split("(")
        args = args.rstrip(")")
        args = [item.strip() for item in args.split(",")]
        finished_arguments = []
        for arg in args:
            is_list = False
            is_optional = False
            pieces = re.split(r" +", arg)
            typehint, argname = pieces

            #Handle special varietations
            if typehint.endswith("*"):
                is_list = True
                typehint = typehint.strip("*")
            if typehint.endswith("?"):
                is_optional = True
                typehint = typehint.strip("?")

            #Fetch typing info
            if hasattr(ast, typehint):
                arg_typing = getattr(ast, typehint)
                arg_typestring = arg_typing.__name__
            else:
                arg_typing, arg_typestring = literal_map[typehint]
            if is_list:
                arg_typestring = "List[{}]".format(arg_typestring)
            if is_optional:
                arg_typestring = "Optional[{}]".format(arg_typestring)

            #Make and store node
            signode = signature_node(argname, arg_typestring, arg_typing, is_list, is_optional)
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

        subclasses = subclasses.strip().strip("\n\n") #Strip end chars
        subclasses = re.sub(r"--.*", "", subclasses) #Strip comments out of file
        subclasses = [item.strip() for item in subclasses.split("|")]
        output_classes = []
        for subclass in subclasses:
            print("building", name, "subclass", subclass)
            if subclass.startswith("("):
                #This does a little rewriting, such that, for example,
                #   comprehension = (expr target, expr iter, expr* ifs, int is_async)
                # will instead be seen as
                #   comprehension = comprehension(expr target, expr iter, expr* ifs, int is_async)
                print('lazy documentation detected')
                subclass = name + subclass
                print("now building", name, "subclass", subclass)


            if "(" in subclass:
                subclassname = next(re.finditer(r'.+(?=\()', subclass)).string
            else:
                subclassname = subclass
            if not hasattr(ast, subclassname):
                continue
            output_classes.append(get_subchild(subclass))
        node = syntax_group(name, getattr(ast, name), output_classes)
        output_groups.append(node)
    return syntax_tree(output_groups)

tree = get_syntactic_tree(grammer)




