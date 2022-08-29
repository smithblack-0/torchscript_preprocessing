import pyparsing as pp


print(pp.alphas)
match = pp.Word("{") + pp.Word("START") + "->" + pp.Word(pp.alphas) + pp.Word("}")
parse_string = " do nothing with {START->Stuff{}{}}"
output = match.scan_string(parse_string)
for match in output:
    print(match)
print(output)