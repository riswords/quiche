from abc import ABC, abstractmethod


class QuicheTree(ABC):
    @abstractmethod
    def value(self):
        pass

    @abstractmethod
    def children(self):
        pass

    @abstractmethod
    def is_pattern_symbol(self):
        pass

    def matches_enode(self, enode):
        if self.value() != enode.key:
            return False
        return True

    def __repr__(self) -> str:
        if self.children():
            return (
                f'({self.value()} {" ".join(str(child) for child in self.children())})'
            )
        else:
            return str(self.value())
