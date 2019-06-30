from ctypes import addressof, pointer, memmove, memset, string_at

from .ctypes_types import ubyte, uword, udword, uqword
from .FPU import flt, dbl, binary80

__all__ = 'Memory',


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
        self.__program_break = 0

        if segment_registers is not None:
            self.segment_override = self.__segment_override_number

    @property
    def program_break(self) -> int:
        return self.__program_break

    @program_break.setter
    def program_break(self, value: int) -> None:
        # print(f'Changing program break: 0x{self.__program_break:08x} => 0x{value:08x}')

        self.__program_break = value

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

    def calc_address(self, offset: int) -> int:
        return self.base + self.__segment_base + offset

    def calc_address_raw(self, offset: int) -> int:
        return self.base + offset

    def get(self, offset: int, size: int, signed=False) -> int:
        if self.__segment_base + offset + size > self.__size or offset < 0:
            raise MemoryError(f"Memory.get: not enough memory (requested address: 0x{offset:08x}, memory available: {self.size} bytes)")

        if size == 4:
            ret = self.types[size].from_address(self.base + self.__segment_base + offset).value

            return ret if not signed else (ret if ret < 2147483648 else ret - 4294967296)
        elif size == 2:
            ret = self.types[size].from_address(self.base + self.__segment_base + offset).value

            return ret if not signed else (ret if ret < 32768 else ret - 65536)
        elif size == 1:
            ret = self.mem[self.__segment_base + offset]

            return ret if not signed else (ret if ret < 128 else ret - 256)

        raise ValueError(
            f'Memory.get(offset={offset:08x}, size={size}): invalid size, please use Memory.get_bytes instead'
        )

    def get_bytes(self, offset: int, size: int) -> bytes:
        if self.__segment_base + offset + size > self.__size or offset < 0:
            raise MemoryError(f"Memory.get: not enough memory (requested address: 0x{offset:08x}, memory available: {self.size} bytes)")

        return bytes(self.mem[self.__segment_base + offset:self.__segment_base + offset + size])

    def kernel_read_string(self, offset: int, size=-1) -> bytes:
        return string_at(self.base + offset, size)

    def get_eip(self, offset: int, size: int, signed=False) -> int:
        if offset + size > self.__size or offset < 0:
            raise MemoryError(f"Memory.get_eip: not enough memory (requested address: 0x{offset:08x}, memory available: {self.size} bytes)")

        if size == 4:
            ret = self.types[size].from_address(self.base + offset).value

            return ret if not signed else (ret if ret < 2147483648 else ret - 4294967296)
        elif size == 2:
            ret = self.types[size].from_address(self.base + offset).value

            return ret if not signed else (ret if ret < 32768 else ret - 65536)
        elif size == 1:
            ret = self.mem[offset]

            return ret if not signed else (ret if ret < 128 else ret - 256)

        return bytes(self.mem[offset:offset + size])

    def get_float(self, offset: int, size: int) -> binary80:
        if self.__segment_base + offset + size // 8 > self.__size or offset < 0:
            raise MemoryError(f"Memory.get: not enough memory (requested address: 0x{offset:08x}, memory available: {self.size} bytes)")

        orig_float = {32: flt, 64: dbl, 80: binary80}[size].from_address(self.base + self.__segment_base + offset)

        if size == 80:
            return orig_float

        return binary80.from_float(orig_float.value)

    def get_float_eip(self, offset: int, size: int) -> binary80:
        if offset + size // 8 > self.__size or offset < 0:
            raise MemoryError(f"Memory.get_eip: not enough memory (requested address: 0x{offset:08x}, memory available: {self.size} bytes)")

        orig_float = {32: flt, 64: dbl, 80: binary80}[size].from_address(self.base + offset)

        if size == 80:
            return orig_float

        return binary80.from_float(orig_float.value)

    def memset(self, offset: int, value: int, count: int) -> int:
        return memset(self.base + offset, value, count) - self.base

    # def set_addr(self, offset: int, size: int, addr: int) -> None:
    #     memmove(self.base + offset, addr, size)

    def set_bytes(self, offset: int, size: int, val: bytes) -> None:
        if self.__segment_base + offset + size > self.__size or offset < 0:
            raise MemoryError(f"Memory.set_bytes: not enough memory (tried to write {size} bytes to address: 0x{offset:08x}, memory available: {self.size} bytes)")

        addr = self.__segment_base + offset
        self.mem[addr:addr + size] = val

    def set(self, offset: int, size: int, val: int) -> None:
        if self.__segment_base + offset + size > self.__size or offset < 0:
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
        else:
            raise RuntimeError(f'Memory.set: invalid size: {size} not in (1, 2, 4). Use Memory.set_bytes instead')

    def set_float(self, offset: int, size: int, val: binary80) -> None:
        if self.__segment_base + offset + size > self.__size or offset < 0:
            raise MemoryError(f"Memory.set: not enough memory (requested address: 0x{offset:08x}, memory available: {self.size} bytes)")

        converted = {4: flt, 8: dbl}[size](float(val))

        addr = self.__segment_base + offset

        self.mem[addr:addr + size] = {4: udword, 8: uqword}[size].from_buffer(converted).value.to_bytes(size, 'little')
