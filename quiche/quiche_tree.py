from abc import ABC, abstractmethod


class QuicheTree(ABC):
    @property
    @abstractmethod
    def value(self):
        pass

    @property
    @abstractmethod
    def children(self):
        pass

    def __repr__(self) -> str:
        if self.children():
            return f'({self.value()} {" ".join(str(child) for child in self.children())})'
        else:
            return str(self.value())
