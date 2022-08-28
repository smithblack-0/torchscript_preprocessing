import regex



regex_input_capture_template = r"([^{open}{close}]*+(?:(?R))*+[^{open}{close}]*)"
regex_specific_capture_template = r"({name})"
regex_general_capture = r"({open}){select}({close})"

open = "{"
close = "}"
subgroup_patterns = ("Start", None)
subgroup_break = "-"

input_capture = regex_input_capture_template.format(open=open, close=close)
select = [input_capture if subgroup_pattern is None
          else regex_specific_capture_template.format(name=subgroup_pattern)
          for subgroup_pattern in subgroup_patterns]
select = subgroup_break.join(select)
pattern = regex_general_capture.format(open=open,
                                       select=select,
                                       close=close)

pattern = regex.compile(pattern)

test_string = "{Start-stuf-f}"
print(regex.findall(pattern, test_string))
match = regex.match(pattern, test_string)
print(match)

if