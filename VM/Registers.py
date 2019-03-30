class Reg32:
    """
    Provides all the 32-, 16- and 8-bit registers of a IA-32 CPU.
    """
    names = "eax ecx edx ebx esp ebp esi edi".split()

    CF, PF, AF, ZF, SF, TF, IF, DF, OF = 0, 2, 4, *range(6, 12)  # EFLAGS bits

    def __init__(self):
        self.allowed_sizes = [4, 2, 1]
        # self.registers = bytearray(self.allowed_sizes[0] * len(Reg32.names))
        self.eflags = 0x02  # initial value according to the Intel Software Development Manual
        self.CS, self.DS, self.SS, self.ES, self.FS, self.GS = [0] * 6  # segment registers

        self.bounds = range(len(Reg32.names))

        reserved_eflags_bits = {1, 3, 5, 15}
        reserved_eflags_bits.update(set(range(22, 32)))

        self.eflags_bounds = set(range(32)) - reserved_eflags_bits

        self.registers = [
            b'\0\0\0\0',  # EAX (000)
            b'\0\0\0\0',  # ECX (001)
            b'\0\0\0\0',  # EDX (010)
            b'\0\0\0\0',  # EBX (011)
            b'\0\0\0\0',  # ESP (100)
            b'\0\0\0\0',  # EBP (101)
            b'\0\0\0\0',  # ESI (110)
            b'\0\0\0\0',  # EDI (111)
        ]
        self.registers = list(map(bytearray, self.registers))

    def get(self, offset: int, size: int) -> bytes:
        """
        Extract `size` bytes and reverse them if byteorder == 'little'
        :param offset: Register number according to the Intel Software Developer Manual
        :param size: Size of the register to read, in bytes.
        :return: The actual bytes read.
        """

        # print(f'Reg32.get({offset:03b}, {size}) -> ', end='')
        if size == 4 or size == 2:
            __tmp = self.registers[offset] #[::-1]
            val = __tmp[:size]
        elif size == 1:
            __tmp = self.registers[offset & 0b011]  # get rid of the first 1 bit
            val = bytes([__tmp[(offset >> 2) & 1]])
        else:
            raise RuntimeError(f"Invalid offset for PyVM.Registers.Reg32.get: {offset}")

        # print(f'{__tmp.hex()} -> {val.hex()}')

        return val

    def set(self, offset: int, value: bytes) -> None:
        """
        Set literal value, reversed in little-endian!
        :param offset:
        :param value:
        :return:
        """

        size = len(value)

        # print(f'Setting {value.hex()}')

        if size == 4:
            self.registers[offset][:] = value
        elif size == 2:
            self.registers[offset][:2] = value
        elif size == 1:
            self.registers[offset & 0b011][(offset >> 2) & 1] = value[0]
        else:
            raise RuntimeError(f"Invalid offset for PyVM.Registers.Reg32.set: {offset}")

    def eflags_get(self, bit: int) -> int:
        """
        Retrieve a specific bit of the EFLAGS register
        :param bit: the number of the bit
        :return:
        """
        assert bit in self.eflags_bounds, 'Reg32.eflags_get: invalid bit number {} (allowed bit numbers: {})'.format(bit, self.eflags_bounds)

        return (self.eflags >> bit) & 1

    def eflags_set(self, bit: int, value: bool) -> None:
        """
        Set a specific bit of the EFLAGS register to some value
        :param bit: the number of the bit
        :param value: boolean
        :return:  None
        """
        if self.eflags_get(bit):
            if not value:
                self.eflags &= ~(1 << bit)
        else:
            if value:
                self.eflags |= 1 << bit


class FReg32:
    names = "st0 st1 st2 st3 st4 st5 st6 st7".split()

    def __init__(self):
        self.allowed_sizes = [8]
        self.registers = bytearray(self.allowed_sizes[0] * len(FReg32.names))

        self.control = 0
        self.status = 0b00_111_00000000000
        self.tag = 0xFFFF

    def _get_st(self, reg_num: int) -> bytes:
        TOP = self.TOP + reg_num

        if TOP >= 0b111:
            raise RuntimeError("The floating-point TOP pointer is messed up!")

        sz = self.allowed_sizes[0]

        s = slice(TOP * sz, (TOP + 1) * sz)
        value = self.registers[TOP * sz:(TOP + 1) * sz]
        #print(f"Actually getting ST{reg_num} ({s}) -> {value}")
        return value

    def _set_st(self, reg_num: int, value: bytes) -> None:
        sz = self.allowed_sizes[0]
        assert len(value) == sz

        TOP = self.TOP + reg_num

        if TOP < 0:
            raise RuntimeError("The floating-point TOP pointer is messed up!")

        s = slice(TOP * sz, (TOP + 1) * sz)

        #print(f"Actually setting ST{reg_num} ({s}) = {value}")
        self.registers[s] = value

    # TODO: generate that with a metaclass
    ST0 = property(lambda self: self._get_st(0), lambda self, val: self._set_st(0, val))
    ST1 = property(lambda self: self._get_st(1), lambda self, val: self._set_st(1, val))
    ST2 = property(lambda self: self._get_st(2), lambda self, val: self._set_st(2, val))
    ST3 = property(lambda self: self._get_st(3), lambda self, val: self._set_st(3, val))
    ST4 = property(lambda self: self._get_st(4), lambda self, val: self._set_st(4, val))
    ST5 = property(lambda self: self._get_st(5), lambda self, val: self._set_st(5, val))
    ST6 = property(lambda self: self._get_st(6), lambda self, val: self._set_st(6, val))
    ST7 = property(lambda self: self._get_st(7), lambda self, val: self._set_st(7, val))

    @property
    def TOP(self) -> int:
        return (self.status >> 11) & 0b111

    @TOP.setter
    def TOP(self, val: int) -> None:
        self.status &= 0b11_000_11111111111  # clear TOP; ugly AF
        self.status |= val << 11  # set TOP back

    def push(self, value: bytes) -> None:
        sz = self.allowed_sizes[0]

        assert len(value) == sz

        TOP = self.TOP

        if TOP == 0:
            raise ValueError("Push onto full stack")

        # print(f"Pushing {value} -> {TOP * sz}:{(TOP + 1) * sz} ({TOP}:{TOP + 1})")

        self.TOP = TOP - 1
        self.ST0 = value

    def pop(self, increase_TOP=True) -> bytearray:
        sz = self.allowed_sizes[0]
        TOP = self.TOP

        if TOP == 0b111:
            raise ValueError("Pop from empty stack")

        # print(f"Popping {TOP * sz}:{(TOP + 1) * sz}")
        ret = self.ST0

        if increase_TOP:
            self.TOP = TOP + 1

        return ret
