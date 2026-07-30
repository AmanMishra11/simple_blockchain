"""Small serialisation helper shared by ledger objects."""
from __future__ import annotations


class Model:
    def to_dict(self):
        return dict(self.__dict__)
