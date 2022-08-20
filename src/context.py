import torch


class start():
    item =3
    item2 = 3
    @classmethod
    def test(cls, val):
        cls.item = val

@torch.jit.script

class class_attribute_date_storage():
    def test(self, val: int):
        self.item = val
    def __init__(self):
        self.item = 3
        self.item2 = 3

@torch.jit.script
class class_attribute_rewrite_test():
    def __getattribute__(self, item):
        if item not in self.__class_storage__.__dict__():
            return super().__getattribute__(item)
        return self.__class_storage__.__getattribute__(item)

    def __init__(self, class_storage: class_attribute_date_storage):
        self.__class_storage__ = class_storage
