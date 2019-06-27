import enum


@enum.unique
class Shift(enum.Enum):
    C_ONE  = 1
    C_CL   = 2
    C_imm8 = 3

    SHL = 4
    SHR = 5
    SAR = 6
    
    
TEST_MODRM = True
if TEST_MODRM:
    from .ModRMParser.ModRM_map import ModRM_map
    
    def new_process_ModRM(self):
        ModRM = self.mem.get_eip(self.eip, 1)
        
        MOD = (ModRM & 0b11000000) >> 6
        RM  = (ModRM & 0b00000111)
        
        if MOD == 0b11:
            REG = (ModRM & 0b00111000) >> 3
            self.eip += 1
            
            return (self.reg, RM), (self.reg, REG)
        
        if RM != 0b100:
            return ModRM_map[ModRM].address(self)
        
        SIB = self.mem.get_eip(self.eip + 1, 1)    
        return ModRM_map[ModRM][SIB].address(self)
    
def old_process_ModRM(self) -> tuple:
    """
    Parses the ModRM byte, which is pointed to by `self.eip`.

    :return: (type1, address1), (type2, address2)
        type:
            self.mem or self.reg
        address:
            Address in memory or the number of the register
    """
    # TODO: 16-bit addressing is not supported!

    ModRM = self.mem.get_eip(self.eip, 1)
    self.eip += 1

    MOD = (ModRM & 0b11000000) >> 6
    REG = (ModRM & 0b00111000) >> 3
    RM  = (ModRM & 0b00000111)

    if MOD == 0b11:
        return (self.reg, RM), (self.reg, REG)

    if RM != 0b100:  # No SIB byte
        if MOD == 0b01:
            addr = self.reg.get(RM, 4, True)
            addr += self.mem.get_eip(self.eip, 1, True)
            self.eip += 1

            return (self.mem, addr), (self.reg, REG)
        if MOD == 0b10:
            addr = self.reg.get(RM, 4, True)
            addr += self.mem.get_eip(self.eip, 4, True)
            self.eip += 4

            return (self.mem, addr), (self.reg, REG)

        # MOD == 0b00
        if RM != 0b101:
            addr = self.reg.get(RM, 4, True)

            return (self.mem, addr), (self.reg, REG)

        # RM == 0b101
        addr = self.mem.get_eip(self.eip, 4, True)
        self.eip += 4

        return (self.mem, addr), (self.reg, REG)

    # RM == 0b100 => SIB byte
    SIB = self.mem.get_eip(self.eip, 1)
    self.eip += 1

    scale = (SIB & 0b11000000) >> 6
    index = (SIB & 0b00111000) >> 3
    base  = (SIB & 0b00000111)

    if MOD == 0b00:
        addr = 0
    elif MOD == 0b01:
        addr = self.mem.get_eip(self.eip, 1, True)
        self.eip += 1
    else:  # MOD == 0b10
        addr = self.mem.get_eip(self.eip, 4, True)
        self.eip += 4

    if index != 0b100:  # if index == 0b100, there's no index
        addr += self.reg.get(index, 4, True) << scale

    if base == 0b101:
        if MOD == 0:
            addr += self.mem.get_eip(self.eip, 4, True)
            self.eip += 4

            return (self.mem, addr), (self.reg, REG)

    # (base != 0b101) or we dropped from the `if` clause above

    addr += self.reg.get(base, 4, True)

    return (self.mem, addr), (self.reg, REG)
    
process_ModRM = new_process_ModRM if TEST_MODRM else old_process_ModRM

def very_old_process_ModRM(self, size1: int, size2=None) -> tuple:
    """
    Parses the ModRM byte, which is pointed to by `self.eip`.

    :param size1: The size of data to read/write from/to the first returned address or register.
    :param size2: The size of data to read/write from/to the second returned register
    :return: (type1, address1, size1), (type2, address2, size2)
        type:
            self.mem or self.reg
        address:
            Address in memory or the number of the register
        size1, size2:
            Exact copies of whatever was passed as arguments
    """
    # TODO: 16-bit addressing is not supported!
    size2 = size2 or size1  # TODO: do we need `size`s at all?

    ModRM = self.mem.get_eip(self.eip, 1)
    self.eip += 1

    MOD = (ModRM & 0b11000000) >> 6
    REG = (ModRM & 0b00111000) >> 3
    RM  = (ModRM & 0b00000111)

    if MOD == 0b11:
        return (self.reg, RM, size1), (self.reg, REG, size2)

    if RM != 0b100:  # No SIB byte
        if MOD == 0b01:
            addr = self.reg.get(RM, 4, True)
            addr += self.mem.get_eip(self.eip, 1, True)
            self.eip += 1

            return (self.mem, addr, size1), (self.reg, REG, size2)
        if MOD == 0b10:
            addr = self.reg.get(RM, 4, True)
            addr += self.mem.get_eip(self.eip, 4, True)
            self.eip += 4

            return (self.mem, addr, size1), (self.reg, REG, size2)

        # MOD == 0b00
        if RM != 0b101:
            addr = self.reg.get(RM, 4, True)

            return (self.mem, addr, size1), (self.reg, REG, size2)

        # RM == 0b101
        addr = self.mem.get_eip(self.eip, 4, True)
        self.eip += 4

        return (self.mem, addr, size1), (self.reg, REG, size2)

    # RM == 0b100 => SIB byte
    SIB = self.mem.get_eip(self.eip, 1)
    self.eip += 1

    scale = (SIB & 0b11000000) >> 6
    index = (SIB & 0b00111000) >> 3
    base  = (SIB & 0b00000111)

    if MOD == 0b00:
        addr = 0
    elif MOD == 0b01:
        addr = self.mem.get_eip(self.eip, 1, True)
        self.eip += 1
    else:  # MOD == 0b10
        addr = self.mem.get_eip(self.eip, 4, True)
        self.eip += 4

    if index != 0b100:  # if index == 0b100, there's no index
        addr += self.reg.get(index, 4, True) << scale

    if base == 0b101:
        if MOD == 0:
            addr += self.mem.get_eip(self.eip, 4, True)
            self.eip += 4

            return (self.mem, addr, size1), (self.reg, REG, size2)

    # (base != 0b101) or we dropped from the `if` clause above

    addr += self.reg.get(base, 4, True)

    return (self.mem, addr, size1), (self.reg, REG, size2)


def sign_extend(num: int, nbytes: int) -> int:
    # TODO: this is basically converting an unsigned number to signed. Maybe rename the function?
    """
    See: https://stackoverflow.com/a/32031543/4354477
    :param num: The integer to sign-extend
    :param nbytes: The number of bytes _in that integer_.
    :return:
    """
    if num < 0:
        return num
    
    sign_bit = 1 << (nbytes * 8 - 1)
    return (num & (sign_bit - 1)) - (num & sign_bit)


def parity(num: int) -> int:
    """
    Calculate the parity of the least significant byte of a number.
    See: https://graphics.stanford.edu/~seander/bithacks.html#ParityWith64Bits
    :param num: The byte to calculate the parity of.
    :return:
    """

    return ((((num & 0xFF) * 0x0101010101010101) & 0x8040201008040201) % 0x1FF) & 1


def MSB(num: int, size: int) -> int:
    """
    Get the most significant bit of a `size`-byte number `num`.
    :param num: A number.
    :param size: The number of bytes in this number.
    :return:
    """

    return (num >> (size * 8 - 1)) & 1


def LSB(num: int) -> int:
    """
    Get the least significant bit of a `size`-byte number `num`.
    :param num: A number.
    :param size: The number of bytes in this number.
    :return:
    """

    return num & 1
