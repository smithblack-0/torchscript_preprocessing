import pyparsing as pp



pattern = pp.Literal("{") + pp.Word(pp.alphas) + pp.Literal("}")
string = " do {match} also match {matching}"
ptn = "{{'{' W:(A-Za-z)} '}'}"
open, close = ("{", "}")
subgroups = (None,)

open, close = ("{", "}")
subgroup_delimitor = "|-|"
pattern = pp.Literal(open)
for i, grammer in enumerate(subgroups):
    # Handle delimiter
    if i > 0:
        pattern = pattern + pp.Suppress(pp.Literal(subgroup_delimitor))

    # Handle grammer case
    if grammer is None:
        pattern = pattern + pp.Word(pp.alphas)  # Capture useful info
    else:
        pattern = pattern + pp.Suppress(pp.Literal(grammer))  # Part of syntax, but not parameters.
pattern = pattern + pp.Literal(close)
for match in pattern.scan_string(string):
    print(match)
