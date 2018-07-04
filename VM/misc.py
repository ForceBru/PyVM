import enum
from .util import to_int, byteorder

@enum.unique
class Shift(enum.Enum):
    C_ONE  = 1
    C_CL   = 2
    C_imm8 = 3

    SHL = 4
    SHR = 5
    SAR = 6
    

def process_ModRM(self, size1, size2):
    '''
    Assumes that 'self.eip' points to ModRM.

    Returns:
            (type, offset, size), (type, offset, size)
            type:
                0 - register
                1 - address
    '''
    ModRM = self.mem.get(self.eip, 1)[0]
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
            addr = to_int(addr, True)
        else:
            # read register
            addr = to_int(self.reg.get(RM, 4), True)
            
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


def sign_extend(number: bytes, nbytes: int) -> bytes:
    return int.from_bytes(number, byteorder, signed=True).to_bytes(nbytes, byteorder, signed=True)
    
def zero_extend(number: bytes, nbytes: int) -> bytes:
  l = len(number)
  assert l <= nbytes
  
  result = bytearray(nbytes)
  
  if byteorder == 'big':
    result[-1:-l - 1:-1] = reversed(number)
  else:
    result[:l] = number
    
  return result


def parity(num: int, nbytes: int) -> bool:
    'Calculate the parity of a byte'
    assert 0 <= num <= 255

    return (((num * 0x0101010101010101) & 0x8040201008040201) % 0x1FF) & 1
