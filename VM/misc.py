import enum

@enum.unique
class Shift(enum.Enum):
    C_ONE  = 1
    C_CL   = 2
    C_imm8 = 3

    SHL = 4
    SHR = 5
    SAR = 6


def process_ModRM(self, size1: int, size2=None):
    size2 = size2 or size1

    ModRM = self.mem.get_eip(self.eip, 1)
    self.eip += 1

    MOD = (ModRM & 0b11000000) >> 6
    REG = (ModRM & 0b00111000) >> 3
    RM  = (ModRM & 0b00000111)


    if MOD == 0b11:
        return (0, RM, size1), (0, REG, size2)

    if RM != 0b100:
        if MOD == 0b01:
            addr = sign_extend(self.reg.get(RM, 4), 4)
            addr += sign_extend(self.mem.get_eip(self.eip, 1), 1)
            self.eip += 1

            return (1, addr, size1), (0, REG, size2)
        if MOD == 0b10:
            addr = sign_extend(self.reg.get(RM, 4), 4)
            addr += sign_extend(self.mem.get_eip(self.eip, 4), 4)
            self.eip += 4

            return (1, addr, size1), (0, REG, size2)

        # MOD == 0b00
        if RM != 0b101:
            addr = sign_extend(self.reg.get(RM, 4), 4)

            return (1, addr, size1), (0, REG, size2)

        # RM == 0b101
        addr = sign_extend(self.mem.get_eip(self.eip, 4), 4)
        self.eip += 4

        return (1, addr, size1), (0, REG, size2)

    # RM == 0b100
    SIB = self.mem.get_eip(self.eip, 1)
    self.eip += 1

    scale = (SIB & 0b11000000) >> 6
    index = (SIB & 0b00111000) >> 3
    base  = (SIB & 0b00000111)

    if MOD == 0b00:
        addr = 0
    elif MOD == 0b01:
        addr = sign_extend(self.mem.get_eip(self.eip, 1), 1)
        self.eip += 1
    else:  # MOD == 0b10
        addr = sign_extend(self.mem.get_eip(self.eip, 4), 4)
        self.eip += 4

    if index != 0b100:
        addr += sign_extend(self.reg.get(index, 4), 4) << scale

    if base == 0b101:
        if MOD == 0:
            addr += sign_extend(self.mem.get_eip(self.eip, 4), 4)
            self.eip += 4

            return (1, addr, size1), (0, REG, size2)

        if MOD == 0b01:
            addr += sign_extend(self.mem.get_eip(self.eip, 1), 1)
            self.eip += 1
        else:  # MOD == 0b10
            addr += sign_extend(self.mem.get_eip(self.eip, 4), 4)
            self.eip += 4

    # (base != 0b101) or we dropped from the `if` clause above

    addr += sign_extend(self.reg.get(base, 4), 4)

    return (1, addr, size1), (0, REG, size2)
    

def process_ModRM_old(self, size1, size2=None):
    '''
    Assumes that 'self.eip' points to ModRM.

    Returns:
            (type, offset, size), (type, offset, size)
            type:
                0 - register
                1 - address
    '''
    if self.address_size < 4:
        raise RuntimeError('16-bit addressing is not supported, apparently')

    if size2 is None:
        size2 = size1

    ModRM = self.mem.get_eip(self.eip, 1)
    # print(f'ModRM: {ModRM:02x} ({ModRM:08b})')
    self.eip += 1
    
    RM  = ModRM & 0b111; ModRM >>= 3
    REG = ModRM & 0b111; ModRM >>= 3
    MOD = ModRM

    # print(f'ModRM: MOD={MOD:02b}, REG={REG:03b}, RM={RM:03b}')
    
    if MOD == 0b11:
        # (register, register)
        return (0, RM, size1), (0, REG, size2)
        
    if RM != 0b100:  # there's no SIB
        if (MOD == 0b00) and (RM == 0b101):
            # read d32 (32-bit displacement)
            addr = self.mem.get(self.eip, 4)
            self.eip += 4
            addr = sign_extend(addr, 4)
        else:
            # read register
            addr = sign_extend(self.reg.get(RM, 4), 4)

            #print(f'ModRM: read address from register = {addr:08x}')
            
        # Read displacement
        # The number of bytes to read (b) depends on (MOD) in the following way:
        #
        # MOD | b
        # 01  | 1
        # 10  | 4
        #
        # This can also be represented as a linear map:
        #     b = 3 * MOD - 2
        # One could write a bunch of if statements to process this, but this function
        # is way simpler
        if (MOD == 0b01) or (MOD == 0b10):
            b = 3 * MOD - 2
            displacement = self.mem.get(self.eip, b)
            self.eip += b
            
            addr += sign_extend(displacement, b)
    else:  # there's a SIB
        SIB = self.mem.get(self.eip, 1)
        self.eip += 1
        _SIB = SIB

        base  = SIB & 0b111; SIB >>= 3
        index = SIB & 0b111; SIB >>= 3
        scale = SIB

        # print(f'SIB: {_SIB:02x}; S={scale:02b}, I={index:03b}, B={base:03b}')
        
        addr = 0

        # add displacement (d8 or d32)
        if MOD == 0b01:
            displacement = self.mem.get(self.eip, 1)
            self.eip += 1

            addr += sign_extend(displacement, 1)
        elif MOD == 0b10:
            displacement = self.mem.get(self.eip, 4)
            self.eip += 4

            addr += sign_extend(displacement, 4)
        
        if index != 0b100:
            addr += sign_extend(self.reg.get(index, 4), 4) << scale
        
        # Addressing modes:
        #
        # MOD bits | Address
        # 00       | [scaled index] + d32 (the latter hasn't been read yet)
        # 01       | [scaled index] + [EBP] + d8 (which has already been read)
        # 10       | [scaled index] + [EBP] + d32 (which has already been read)
        if (base == 0b101) and (MOD == 0b00):
            # add a d32
            d32 = self.mem.get(self.eip, 4) 
            self.eip += 4
            
            addr += sign_extend(d32, 4)
        else:
            # add [base]
            addr += sign_extend(self.reg.get(base, 4), 4)
                    
    RM, R = (1, addr, size1), (0, REG, size2)

    return RM, R


def sign_extend(num: int, nbytes: int) -> int:
    # TODO: this is basically converting an unsigned number to signed. Maybe rename the function?
    '''
    See: https://stackoverflow.com/a/32031543/4354477
    :param num: The integer to sign-extend
    :param nbytes: The number of bytes _in that integer_.
    :return:
    '''
    if num < 0:
        return num
    
    sign_bit = 1 << (nbytes * 8 - 1)
    return (num & (sign_bit - 1)) - (num & sign_bit)


def zero_extend(number: int, nbytes: int) -> int:
    # TODO: to be removed because we're dealing with integers already, and zero-extension is done automatically.
    return number


def parity(num: int) -> int:
    '''
    Calculate the parity of a byte. See: https://graphics.stanford.edu/~seander/bithacks.html#ParityWith64Bits
    :param num: The byte to calculate the parity of.
    :return:
    '''
    assert 0 <= num <= 255

    return (((num * 0x0101010101010101) & 0x8040201008040201) % 0x1FF) & 1


def MSB(num: int, size: int) -> bool:
    """
    Get the most significant bit of a `size`-byte number `num`.
    :param num: A number.
    :param size: The number of bytes in this number.
    :return:
    """

    return bool(num >> (size * 8 - 1))


def LSB(num: int, size: int) -> bool:
    """
    Get the least significant bit of a `size`-byte number `num`.
    :param num: A number.
    :param size: The number of bytes in this number.
    :return:
    """

    return bool(num & 1)
