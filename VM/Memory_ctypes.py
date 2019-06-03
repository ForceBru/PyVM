from ctypes import addressof, pointer, memmove
from .ctypes_types import ubyte, uword, udword

__all_ = 'Memory',


class Memory:
    types = [None, ubyte, uword, None, udword]

    def __init__(self, memsz: int, segment_registers=None):
        self.sreg = segment_registers

        self.__size = 0
        self.__segment_override_number = 3  # DS
        self.mem = self.mem_ptr = None
        self.base = 0
        self.__segment_base = 0

        self.size = memsz
        self.segment_override = self.__segment_override_number

    @property
    def size(self):
        return self.__size

    @size.setter
    def size(self, memsz: int):
        assert memsz > 0

        self.mem = (ubyte * memsz)()

        self.base = addressof(self.mem)
        self.mem_ptr = pointer(self.mem)
        self.__size = memsz

    @property
    def segment_override(self) -> int:
        return self.__segment_override_number

    @segment_override.setter
    def segment_override(self, segment_number: int) -> None:
        sreg = self.sreg.get(segment_number)

        self.__segment_base = sreg.hidden.base

    def get(self, offset: int, size: int) -> int:
        if self.__segment_base + offset + size > self.__size or offset < 0:
            raise MemoryError(f"Memory.get: not enough memory (requested address: 0x{offset:08x}, memory available: {self.size} bytes)")

        # add segments support here
        if size == 4 or size == 2:
            return self.types[size].from_address(self.base + self.__segment_base + offset).value
        elif size == 1:
            return self.mem[self.__segment_base + offset]
        return bytes(self.mem[self.__segment_base + offset:self.__segment_base + offset + size])

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
        if self.__segment_base + offset + size > self.__size:
            raise MemoryError(f"Memory.set_bytes: not enough memory (tried to write {size} bytes to address: 0x{offset:08x}, memory available: {self.size} bytes)")

        addr = self.__segment_base + offset
        self.mem[addr:addr + size] = val

        #if size < 20:
            #print(f'Memory.set_bytes({offset:08x}, val={val})')

    def set(self, offset: int, size: int, val: int) -> None:
        if self.__segment_base + offset + size >= self.__size or offset < 0:
            raise MemoryError(f"Memory.set: not enough memory (requested address: 0x{offset:08x}, memory available: {self.size} bytes)")

        addr = self.__segment_base + offset
        if size == 4:
            # faster than byte unpacking with shifts
            self.mem[addr:addr + 4] = (val & 0xFFFFFFFF).to_bytes(4, 'little')
        elif size == 2:
            # faster than `(val & 0xFFFF).to_bytes(2, 'little')`
            self.mem[addr:addr + 2] = val & 0xFF, (val >> 8) & 0xFF  # (val & 0xFFFF).to_bytes(2, 'little')
        elif size == 1:
            self.mem[addr] = val
