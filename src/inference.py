"""

Contains the code for the inference engine, utilized

"""

def infer_feature(node: StackSupportNode, name: str):
    """
    Attempt to infer any information possible about where
    and how the given node is defined

    :param node: The node to infer from
    :param name: The name of what to look for
    :return: A generator of options
    """
    def predicate(context: StackSupportNode, node: ast.AST)->bool:
        if not isinstance(node, ast.Name):
            return False
        if node.id != name:
            return False
        if not isinstance(node.ctx, ast.Store):
            return False
        return True

    for context, node in node.get_reverse_iterator():
        if not isinstance(node, ast.AST):
            continue
        context = context.push(node)
        captures = capture(node, predicate, context=context)
        for subcontext, subnode in captures:

            print(subcontext, subnode)