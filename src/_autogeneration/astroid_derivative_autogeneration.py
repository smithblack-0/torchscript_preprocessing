"""

This script generates a sequence of nodes from
the astroid project which in turn will possess
additional properties. In particular, these nodes
are designed to be used to build a new syntax tree,
and provide support for exactly this

"""

#The basic idea is a semimutable object will exist with helper
#methods to aid in construction. Constructing new nodes is
#an immutable operation - once something has been committed, it
#is there forever. Iterators exist to go over currrent content, and
#the context support node has a commit method to place info
#back into the correct place given the field and the name.


