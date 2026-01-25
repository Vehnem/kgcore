from abc import ABC, abstractmethod
from typing import List


class KGBackend(ABC):
    """
    Base backend interface. Concrete backends (RDF, PG, ...) subclass this.
    """
    supported_model_families: List[str] = []

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def connect(self) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...