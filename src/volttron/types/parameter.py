from dataclasses import dataclass
from typing import Any


@dataclass
class Parameter:
    key: str
    value: Any
    
    def __hash__(self) -> int:
        return self.key.__hash__()