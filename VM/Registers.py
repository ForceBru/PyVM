class Reg32:
    """
    Provides all the 32-, 16- and 8-bit registers of a IA-32 CPU.
    """
    names = "eax ecx edx ebx esp ebp esi edi".split()

    CF, PF, AF, ZF, SF, TF, IF, DF, OF = 0, 2, 4, *range(6, 12)  # EFLAGS bits

    def __init__(self):
        self.allowed_sizes = [4, 2, 1]
        self.registers = bytearray(self.allowed_sizes[0] * len(Reg32.names))
        self.eflags = 0x02  # initial value according to the Intel Software Development Manual
        self.CS, self.DS, self.SS, self.ES, self.FS, self.GS = [0] * 6  # segment registers

        self.bounds = range(len(Reg32.names))

        reserved_eflags_bits = {1, 3, 5, 15}
        reserved_eflags_bits.update(set(range(22, 32)))

        self.eflags_bounds = set(range(32)) - reserved_eflags_bits

    def get(self, offset: int, size: int) -> bytes:
        """
        :param offset: defined in the Intel Software Development Manual; in a nutshell, it's a unique number corresponding
        to each register.
        :param size: the size of a register in bytes. This alllowes to distinguish between registers that have the same offset.
        :return: the value of the requested register.
        """
        assert offset in self.bounds, 'Reg32.get: register ({}) not in bounds ({})'.format(offset, self.bounds)
        assert size in self.allowed_sizes, 'Reg32.get: invalid size {} (allowed sizes: {})'.format(size, self.allowed_sizes)

        if size == self.allowed_sizes[2]:
            start = (offset % self.allowed_sizes[0] + 1) * self.allowed_sizes[0] - size - offset // self.allowed_sizes[0]
        else:
            start = (offset + 1) * self.allowed_sizes[0] - size

        return self.registers[start:start + size]

    def set(self, offset: int, value: bytes) -> None:
        """

        :param offset: the same as above
        :param value: the value to be written to the register. Its size determines the register to be used.
        :return: None
        """
        size = len(value)
        assert offset in self.bounds, 'Reg32.set: register ({}) not in bounds ({})'.format(offset, self.bounds)
        assert size in self.allowed_sizes, 'Reg32.set: invalid size {} (allowed sizes: {})'.format(size, self.allowed_sizes)

        if size == self.allowed_sizes[2]:
            start = (offset % self.allowed_sizes[0] + 1) * self.allowed_sizes[0] - size - offset // self.allowed_sizes[0]
        else:
            start = (offset + 1) * self.allowed_sizes[0] - size

        self.registers[start:start + size] = value

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
