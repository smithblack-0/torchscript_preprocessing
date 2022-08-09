"""

An implimentation of a tree regex engine using syntax heavily
inspired by tregex:

https://nlp.stanford.edu/manning/courses/ling289/Tregex.html


Examples:

A >_{3} B: Child order operator. B is a child o
A $ B: B is a child of A. child pos operator.

A > B >>_{3} C: A is a child of B. B's third post sibling is C


A > B: A's immediate child is B.
A >> B: A's immediate descendent is B

A #> B: A's immediate sibling is



A >{3} B: A's third descendent is B
A >>{3} B: A's third descendent is B





A > B >>_{3} C: A has a child which is B

Syntax:



Boolean and Capturing

@Name(A): Capture A as Name.
!A: Negate A
A | B: A or B
A & B: A and B
@Name: Utilize capture of name "Name"

Basic traversal and manipulation.

A > B: node A is an immediate parent of B
A < B: node A is an immediate child of B
A >> B : node A is an immediate prior sibling of B
A << B: node A is an immediate post sibling of B
A == B: node  A is B

Quantifiers: They quantify Traversal operators.

X _f: First
X _l: Last
X _*: Zero or more
X _{n}: exactly n times
X _{n,}: At least n times
X _{,n}: No more than n
X _{n, m}: At least n but no more than m

#Compound examples

A >_f B: A is the root node from B
A <_f B: A is the first child of B


#Examples

A > B: A is immediate parent of B
A >? B: A is parent of B after one or more node
A >[3] B: A is child of B after 3 nodes.
A >[3-7]: A is child of B after 3-7 nodes.
A $ B: A is a sibling of B
A $> B: A immediately preceeds B
A $>[3] B: A precedes B by 3 nodes
A $>? B: A precedes B by one or more node
A $< B: A immediately follows B
A $<? B: A follows B after one or more nodes
A $<[3] B: A follows B after 3 nodes

$A #Parent of A



"""

from enum import Enum

## posfix converter


def toPostfix(infix):
    stack = []
    postfix = ''

    for c in infix:
        if isOperand(c):
            postfix += c
        else:
            if isLeftParenthesis(c):
                stack.append(c)
            elif isRightParenthesis(c):
                operator = stack.pop()
                while not isLeftParenthesis(operator):
                    postfix += operator
                    operator = stack.pop()
            else:
                while (not isEmpty(stack)) and hasLessOrEqualPriority(c,peek(stack)):
                    postfix += stack.pop()
                stack.append(c)

    while (not isEmpty(stack)):
        postfix += stack.pop()
    return postfix

##