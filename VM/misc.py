import enum
from .util import to_int, byteorder, to_signed

@enum.unique
class Shift(enum.Enum):
    C_ONE  = 1
    C_CL   = 2
    C_imm8 = 3

    SHL = 4
    SHR = 5
    SAR = 6
    

def process_ModRM(self, size1, size2=None):
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
    self.eip += 1
    
    RM  = ModRM & 0b111; ModRM >>= 3
    REG = ModRM & 0b111; ModRM >>= 3
    MOD = ModRM
    
    if MOD == 0b11:
        # (register, register)
        return (0, RM, size1), (0, REG, size2)
        
    if RM != 0b100:  # there's no SIB
        if (MOD == 0b00) and (RM == 0b101):
            # read d32 (32-bit displacement)
            addr = self.mem.get(self.eip, 4)
            self.eip += 4
            addr = to_signed(addr, 4)
        else:
            # read register
            addr = to_signed(self.reg.get(RM, 4), 4)
            
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
            
            addr += to_int(displacement, True)
    else:  # there's a SIB
        SIB = self.mem.get(self.eip, 1)[0]
        self.eip += 1

        base  = SIB & 0b111; SIB >>= 3
        index = SIB & 0b111; SIB >>= 3
        scale = SIB
        
        addr = 0
        
        # add displacement (d8 or d32)
        if (MOD == 0b01) or (MOD == 0b10):
            b = 3 * MOD - 2 # see formula above
            displacement = self.mem.get(self.eip, b)
            self.eip += b
            
            addr += to_int(displacement, True)
        
        if index != 0b100:
            addr += to_int(self.reg.get(index, 4), True) << scale
        
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
            
            addr += to_int(d32, True)
        else:
            # add [base]
            addr += to_int(self.reg.get(base, 4), True)
                    
    RM, R = (1, addr, size1), (0, REG, size2)

    return RM, R


def sign_extend_bytes(number: bytes, nbytes: int) -> bytes:
    return int.from_bytes(number, byteorder, signed=True).to_bytes(nbytes, byteorder, signed=True)


def sign_extend(value: int, bytes: int) -> int:
    '''
    See: https://stackoverflow.com/a/32031543/4354477
    :param value:
    :param bytes:
    :return:
    '''

    raise NotImplementedError("This does not work because it needs one more argument. Like 'extend from this size to this size'")
    if bytes == 1:
        return value  # TODO: right?
    if bytes == 2:
        sign_bit = 1 << (16 - 1)
    elif bytes == 4:
        sign_bit = 1 << (32 - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)


def zero_extend_bytes(number: bytes, nbytes: int) -> bytes:
    return int.from_bytes(number, byteorder, signed=False).to_bytes(nbytes, byteorder, signed=False)

def zero_extend(number: int, nbytes: int) -> int:
    return number


def parity(num: int, nbytes: int) -> bool:
    'Calculate the parity of a byte'
    assert 0 <= num <= 255

    return bool((((num * 0x0101010101010101) & 0x8040201008040201) % 0x1FF) & 1)


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
