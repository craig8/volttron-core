# works in Python 2 & 3
from dataclasses import dataclass


class _Singleton(type):
    """ A metaclass that creates a Singleton base class when called. """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Singleton(_Singleton('SingletonMeta', (object, ), {})):
    pass


if __name__ == '__main__':

    @dataclass
    class Logger(Singleton):
        alpha: str
        beta: str

    a = Logger(alpha='5', beta='6')
    b = Logger(alpha='9', beta='10')

    print(id(a), " and ", id(b))
    assert a == b

    print(a, b)
