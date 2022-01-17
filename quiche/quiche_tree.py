from abc import ABC, abstractmethod


class QuicheTree(ABC):
    @abstractmethod
    def value(self):
        pass

    @abstractmethod
    def children(self):
        pass

    def __repr__(self) -> str:
        if self.children():
            return f'({self.value()} {" ".join(str(child) for child in self.children())})'
        else:
            return str(self.value())
