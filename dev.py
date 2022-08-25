from typing import List


test_extract = "   {self.{var_name} = {var_frame_name}, HfooH } stuff {hello}"


def get_format_names(template: str):
    """Gets format names out of strings. Respects balancing"""
    depth = 0
    start = 0
    position = 0
    outputs: List[str] = []
    while True:
        next_open_index = template.find("{", position)
        next_close_index = template.find("}", position)
        if next_close_index == -1:
            # Done with iteration
            break
        position = next_open_index if next_open_index < next_close_index\
            and next_open_index != -1 else next_close_index
        if position == next_open_index:
            if depth == 0:
                start = position
            depth += 1
        else:
            depth -= 1

        position += 1
        if depth == 0:
            stringslice = template[start+1:position-1]
            outputs.append(stringslice)
    return outputs

print(get_format_names(test_extract))