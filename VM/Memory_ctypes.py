from ctypes import addressof, pointer, memmove
from .ctypes_types import ubyte, uword, udword

__all_ = 'Memory',


class Memory:
    types = [None, ubyte, uword, None, udword]

    def __init__(self, memsz: int, registers=None):
        self.mem = (ubyte * memsz)()

        self.base = addressof(self.mem)
        self.mem_ptr = pointer(self.mem)
        self.__size = memsz

    @property
    def size(self):
        return self.__size

    @size.setter
    def size(self, memsz: int):
        self.mem = (ubyte * memsz)()

        self.base = addressof(self.mem)
        self.mem_ptr = pointer(self.mem)
        self.__size = memsz

    def get(self, offset: int, size: int) -> int:
        # add segments support here
        if size == 4 or size == 2:
            return self.types[size].from_address(self.base + offset).value
        elif size == 1:
            return self.mem[offset]
        return bytes(self.mem[offset:offset + size])

    def get_eip(self, offset: int, size: int) -> int:
        if size == 4 or size == 2:
            return self.types[size].from_address(self.base + offset).value
        elif size == 1:
            return self.mem[offset]
        return bytes(self.mem[offset:offset + size])

    def set_addr(self, offset: int, size: int, addr: int) -> None:
        memmove(self.base + offset, addr, size)

    def set_bytes(self, offset: int, size: int, val: bytes) -> None:
        self.mem[offset:offset + size] = val

    def set(self, offset: int, size: int, val: int) -> None:
        if size == 4:
            # faster than byte unpacking with shifts
            self.mem[offset:offset + 4] = (val & 0xFFFFFFFF).to_bytes(4, 'little')
        elif size == 2:
            # faster than `(val & 0xFFFF).to_bytes(2, 'little')`
            self.mem[offset:offset + 2] = val & 0xFF, (val >> 8) & 0xFF  # (val & 0xFFFF).to_bytes(2, 'little')
        elif size == 1:
            self.mem[offset] = val
