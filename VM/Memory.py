# Import modules
from ctypes import addressof, pointer, memmove, memset, string_at
from .ctypes_types import ubyte, uword, udword, uqword
from .FPU import flt, dbl, binary80

__all__ = 'Memory',

# Define memory class
class Memory:
    types = [None, ubyte, uword, None, udword] # Define types

    def __init__(self, memsz: int, segment_registers=None):
        self.sreg = segment_registers

        self.__size = 0                     # Define size
        self.__segment_override_number = 3  # DS
        self.mem = self.mem_ptr = None
        self.base = 0                       # Define base
        self.__segment_base = 0

        self.size = memsz
        self.__program_break = 0

        if segment_registers is not None:
            self.segment_override = self.__segment_override_number
    
    # Define program break propertys 
    @property
    def program_break(self) -> int:
        return self.__program_break  

    @program_break.setter
    def program_break(self, value: int) -> None:
        # print(f'Changing program break: 0x{self.__program_break:08x} => 0x{value:08x}')

        self.__program_break = value
    
    # Define return size property
    @property
    def size(self):
        return self.__size
    
    # Define size setter
    @size.setter
    def size(self, memsz: int):
        assert memsz > 0

        self.mem = (ubyte * memsz)()

        self.base = addressof(self.mem)
        self.mem_ptr = pointer(self.mem)
        self.__size = memsz
    
    # Define segment override property
    @property
    def segment_override(self) -> int:
        return self.__segment_override_number # Return segment override number
    
    # Define segment override setter
    @segment_override.setter
    def segment_override(self, segment_number: int) -> None:
        sreg = self.sreg.get(segment_number)

        self.__segment_base = sreg.hidden.base

    def asan_raw(self, offset: int, size: int):
        """
        Check if it is valid to access `size` bytes at address `offset` withing the current code segment.
        :param offset: The accessed address.
        :param size: The amount of bytes to be accessed.
        :return: Raises an exception if the access is invalid.
        """
        if offset > self.__size or offset + size > self.__size:
            # Raise Mem Error if size is of an incorrect value
            raise MemoryError(
                f'Not enough memory (tried to write to address range '
                f'0x{offset:08x}-0x{offset + size:08x} ({size} bytes), maximum address: 0x{self.size:08x} bytes)'
            )
        
        # Mem invalid address failure 
        assert offset >= 0, f'Invalid memory address: {hex(offset)}'
    
    # Preform same task as above w/ non-raw conditions 
    def asan(self, offset: int, size: int):
        """
        Check if it is valid to access `size` bytes at address `offset` within the current data segment.
        :param offset: The accessed address.
        :param size: The amount of bytes to be accessed.
        :return: Raises an exception if the access is invalid.
        """
        if self.__segment_base + offset > self.__size or self.__segment_base + offset + size > self.__size:
            raise MemoryError(
                f'Not enough memory (tried to write to address range 0x{offset:08x}-0x{offset + size:08x} '
                f'({size} bytes), maximum address: 0x{self.size:08x} bytes)'
            )

        assert offset >= 0, f'Invalid memory address: {hex(offset)}'
    
    # Calculate non-raw address
    def calc_address(self, offset: int) -> int:
        return self.base + self.__segment_base + offset
    # Calculate raw address
    def calc_address_raw(self, offset: int) -> int:
        return self.base + offset
    
    # preform a simalar task to asan functions.
    def get(self, offset: int, size: int, signed=False) -> int:
        # self.asan(offset, size) -> pasted here for speed
        if self.__segment_base + offset > self.__size or self.__segment_base + offset + size > self.__size:
            raise MemoryError(
                f'Not enough memory (tried to write to address range 0x{offset:08x}-0x{offset + size:08x} '
                f'({size} bytes), maximum address: 0x{self.size:08x} bytes)'
            )

        assert offset >= 0, f'Invalid memory address: {hex(offset)}'
        
        # Define `ret` (conditional based off of size). 
        if size == 4:
            ret = self.types[size].from_address(self.base + self.__segment_base + offset).value

            return ret if not signed else (ret if ret < 2147483648 else ret - 4294967296)
        elif size == 2:
            ret = self.types[size].from_address(self.base + self.__segment_base + offset).value

            return ret if not signed else (ret if ret < 32768 else ret - 65536)
        elif size == 1:
            ret = self.mem[self.__segment_base + offset]

            return ret if not signed else (ret if ret < 128 else ret - 256)
        
        # Mem invalid size error. 
        raise ValueError(
            f'Memory.get(offset={offset:08x}, size={size}): invalid size, please use Memory.get_bytes instead'
        )
    
    # Define get bytes function, returns byets. 
    def get_bytes(self, offset: int, size: int) -> bytes:
        # self.asan(offset, size) -> pasted here for speed
        if self.__segment_base + offset > self.__size or self.__segment_base + offset + size > self.__size:
            raise MemoryError(
                f'Not enough memory (tried to write to address range 0x{offset:08x}-0x{offset + size:08x} '
                f'({size} bytes), maximum address: 0x{self.size:08x} bytes)'
            )

        assert offset >= 0, f'Invalid memory address: {hex(offset)}'

        return bytes(self.mem[self.__segment_base + offset:self.__segment_base + offset + size])
    
    # Function used to return kernel info? 
    def kernel_read_string(self, offset: int, size=-1) -> bytes:
        return string_at(self.base + offset, size)
    
    
    def get_eip(self, offset: int, size: int, signed=False) -> int:
        # self.asan_raw(offset, size) -> pasted here for speed
        if offset > self.__size or offset + size > self.__size:
            # Out of mem error
            raise MemoryError(
                f'Not enough memory (tried to write to address range '
                f'0x{offset:08x}-0x{offset + size:08x} ({size} bytes), maximum address: 0x{self.size:08x} bytes)'
            )

        assert offset >= 0, f'Invalid memory address: {hex(offset)}'
        
        # Define ret as a value from address. 
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
    
    # Function used to return the orig float (local var). 
    def get_float(self, offset: int, size: int) -> binary80:
        # self.asan(offset, size) -> pasted here for speed
        if self.__segment_base + offset > self.__size or self.__segment_base + offset + size // 8 > self.__size:
            raise MemoryError(
                f'Not enough memory (tried to write to address range 0x{offset:08x}-0x{offset + size:08x} '
                f'({size // 8} bytes), maximum address: 0x{self.size:08x} bytes)'
            )

        assert offset >= 0, f'Invalid memory address: {hex(offset)}'

        orig_float = {32: flt, 64: dbl, 80: binary80}[size].from_address(self.base + self.__segment_base + offset)

        if size == 80:
            return orig_float

        return binary80.from_float(orig_float.value)
    
    # Return orig float (for eip)
    def get_float_eip(self, offset: int, size: int) -> binary80:
        # self.asan_raw(offset, size) -> pasted here for speed
        if offset > self.__size or offset + size > self.__size:
            raise MemoryError(
                f'Not enough memory (tried to write to address range '
                f'0x{offset:08x}-0x{offset + size:08x} ({size} bytes), maximum address: 0x{self.size:08x} bytes)'
            )

        assert offset >= 0, f'Invalid memory address: {hex(offset)}'

        orig_float = {32: flt, 64: dbl, 80: binary80}[size].from_address(self.base + offset)

        if size == 80:
            return orig_float

        return binary80.from_float(orig_float.value)
     
    # Return memset value of base and offset 
    def memset(self, offset: int, value: int, size: int) -> int:
        # self.asan_raw(offset, size) -> pasted here for speed
        if offset > self.__size or offset + size > self.__size:
            raise MemoryError(
                f'Not enough memory (tried to write to address range '
                f'0x{offset:08x}-0x{offset + size:08x} ({size} bytes), maximum address: 0x{self.size:08x} bytes)'
            )

        assert offset >= 0, f'Invalid memory address: {hex(offset)}'

        return memset(self.base + offset, value, size) - self.base

    # def set_addr(self, offset: int, size: int, addr: int) -> None:
    #     memmove(self.base + offset, addr, size)
    
    # Set mem in bytes
    def set_bytes(self, offset: int, size: int, val: bytes) -> None:
        # self.asan(offset, size) -> pasted here for speed
        if self.__segment_base + offset > self.__size or self.__segment_base + offset + size > self.__size:
            raise MemoryError(
                f'Not enough memory (tried to write to address range 0x{offset:08x}-0x{offset + size:08x} '
                f'({size} bytes), maximum address: 0x{self.size:08x} bytes)'
            )

        assert offset >= 0, f'Invalid memory address: {hex(offset)}'

        addr = self.__segment_base + offset
        self.mem[addr:addr + size] = val
    
    # Set mem 
    def set(self, offset: int, size: int, val: int) -> None:
        # self.asan(offset, size) -> pasted here for speed
        if self.__segment_base + offset > self.__size or self.__segment_base + offset + size > self.__size:
            raise MemoryError(
                f'Not enough memory (tried to write to address range 0x{offset:08x}-0x{offset + size:08x} '
                f'({size} bytes), maximum address: 0x{self.size:08x} bytes)'
            )

        assert offset >= 0, f'Invalid memory address: {hex(offset)}'

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
    
    # Set mem as a float
    def set_float(self, offset: int, size: int, val: binary80) -> None:
        # self.asan(offset, size) -> pasted here for speed
        if self.__segment_base + offset > self.__size or self.__segment_base + offset + size > self.__size:
            raise MemoryError(
                f'Not enough memory (tried to write to address range 0x{offset:08x}-0x{offset + size:08x} '
                f'({size} bytes), maximum address: 0x{self.size:08x} bytes)'
            )

        assert offset >= 0, f'Invalid memory address: {hex(offset)}'

        converted = {4: flt, 8: dbl}[size](float(val))

        addr = self.__segment_base + offset

        self.mem[addr:addr + size] = {4: udword, 8: uqword}[size].from_buffer(converted).value.to_bytes(size, 'little')

