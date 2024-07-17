from abc import ABC, abstractmethod
from typing import Any

class Storage(ABC):
    @abstractmethod
    def id(self) -> str:
        ...

    @abstractmethod
    def write(self, data: Any) -> bool | None:
        ...


