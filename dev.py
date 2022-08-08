import torch


#Test code
def redirect():
    return 4
source = """\
def get_4():
    return redirect()
"""
with StringSourceModule(source, globals(), locals()) as module:
    get = torch.jit.script(module.get_4)
    print(get())




