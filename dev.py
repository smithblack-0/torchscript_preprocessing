import pyparsing as pp



pattern = pp.Literal("{") + pp.Word(pp.alphas) + pp.Literal("}")
string = " do <Match> while matching <Match|=|Stuff>"
ptn = "{{'{' W:(A-Za-z)} '}'}"
open, close = ("<", ">")
subgroups = ("Match", None)

open, close = ("<", ">")
subgroup_delimitor = "|=|"
pattern = pp.Literal(open)

for i, grammer in enumerate(subgroups):
    # Handle delimiter
    if i > 0:
        pattern = pattern + pp.Suppress(pp.Literal(subgroup_delimitor))

    # Handle grammer case
    if grammer is None:
        pattern = pattern + pp.nestedExpr(open, close, ...)
    else:
        pattern = pattern + pp.Suppress(pp.Literal(grammer))  # Part of syntax, but not parameters.
pattern = pattern + pp.Literal(close)
print(pattern)
for match in pattern.scan_string(string):
    results, _, _ = match
    print(results)


nested_str = "<<>test <a>>"

ignore_tier = pp.Literal("<") + ... + pp.Literal(">")
expression = pp.Literal("<") + pp.SkipTo(pp.Literal(">"), ignore=ignore_tier) + pp.Literal(">")
for match in expression.scan_string(nested_str):
    print(match)