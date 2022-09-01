

"""

The preprocessing module is responsible
for executing the actual process of
preprocessing using the defined rewriters.

It is also responsible for defining the interface
by which it is the case that subordinate
rewriters can request and otherwise commit modifications.

Modifications and actions with the existing tree are performed
on a stack, with the modifications resolving in the reverse order
that they are defined. It is the case that a modification may be
defined to match one of several conditions, and when so matching
will then be executed in stack order. The modification chain is capable
of executing said stack, at any moment, in order to build a copy of the
current features.

It is the case the stack is capable of addressing further up
the node chain as is required.

---- design ---

parsing occurs as a once-through pass
with an auxiliary stack as a helper. It is
possible to,


---- requirements ----

* Load rewriting entities
* For each node and node's children:
    * Recurse
    * Ask rewriting entities if rewrite is needed.
    * If yes, hand over ResolutionStack, Node for rewriting
    * Get results, and commit to stack at appropriate locations. 
* Build current stack level, then return.

Interactions:

Stack:
    * Pushed to
    * Popped from
    * Push can be a Delay function.
*

"""

class NodeBuilder():
    """
    Can build a

    """


class ResolutionNode:
    """
    
    """

class ResolutionBuilder():
    """
    The builder entity.
    """
    ### Contains stack building and collapsing abilities
    ### Pushing to the builder will create a new layer
    ### Popping from it will result in an associated node being built.




class ResolutionStack:
    """

    """
    def pin(self, name: , expiration_height: str):
