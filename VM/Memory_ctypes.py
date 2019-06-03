from ctypes import addressof, pointer, memmove
from .ctypes_types import ubyte, uword, udword

__all_ = 'Memory',


class Memory:
    types = [None, ubyte, uword, None, udword]

    def __init__(self, memsz: int, registers=None):
        self.mem = (ubyte * memsz)()

        self.base = addressof(self.mem)
        self.mem_ptr = pointer(self.mem)
        self.program_break = 0
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
        if offset + size > self.__size or offset < 0:
            raise MemoryError(f"Memory.get: not enough memory (requested address: 0x{offset:08x}, memory available: {self.size} bytes)")

        # add segments support here
        if size == 4 or size == 2:
            return self.types[size].from_address(self.base + offset).value
        elif size == 1:
            return self.mem[offset]
        return bytes(self.mem[offset:offset + size])

    def get_eip(self, offset: int, size: int) -> int:
        if offset + size > self.__size:
            raise MemoryError(f"Memory.get_eip: not enough memory (requested address: 0x{offset:08x}, memory available: {self.size} bytes)")

        if size == 4 or size == 2:
            return self.types[size].from_address(self.base + offset).value
        elif size == 1:
            return self.mem[offset]
        return bytes(self.mem[offset:offset + size])

    def set_addr(self, offset: int, size: int, addr: int) -> None:
        memmove(self.base + offset, addr, size)

    def set_bytes(self, offset: int, size: int, val: bytes) -> None:
        if offset + size > self.__size:
            raise MemoryError(f"Memory.set_bytes: not enough memory (tried to write {size} bytes to address: 0x{offset:08x}, memory available: {self.size} bytes)")

        self.mem[offset:offset + size] = val

    def set(self, offset: int, size: int, val: int) -> None:
        if offset + size > self.__size:
            raise MemoryError(f"Memory.set: not enough memory (requested address: 0x{offset:08x}, memory available: {self.size} bytes)")

        if size == 4:
            # faster than byte unpacking with shifts
            self.mem[offset:offset + 4] = (val & 0xFFFFFFFF).to_bytes(4, 'little')
        elif size == 2:
            # faster than `(val & 0xFFFF).to_bytes(2, 'little')`
            self.mem[offset:offset + 2] = val & 0xFF, (val >> 8) & 0xFF  # (val & 0xFFFF).to_bytes(2, 'little')
        elif size == 1:
            self.mem[offset] = val
