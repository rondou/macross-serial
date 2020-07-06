from typing import Dict, Type, TypeVar

T: Type = TypeVar('T')


class Singleton(type):
    _instances: Dict[Type[T], T] = dict()

    def __call__(cls: Type[T], *args, **kwargs) -> T:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
