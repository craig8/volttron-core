from collections import defaultdict
from dataclasses import dataclass

from dataclass_wizard import JSONWizard


@dataclass
class MyClass(JSONWizard):
    my_list: list[str]
    my_dict: defaultdict[str, list[int]]
    my_tuple: tuple[int | str, ...]


if __name__ == '__main__':
    data = {'my_list': ['testing'], 'my_dict': {'key': [1, 2, '3']}, 'my_tuple': (1, '2')}

    c = MyClass.from_dict(data)

    print(c.to_json(indent=2))
    #print(repr(c))
    # prints:
    #   MyClass(my_list=['testing'], my_dict=defaultdict(<class 'list'>, {'key': [1, 2, 3]}), my_tuple=(1, '2'))
