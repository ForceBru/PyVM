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
        return (0, RM, size1), (0, REG, size2)
        
    if RM != 0b100:  # there's no SIB
        if (MOD == 0b00) and (RM == 0b101):
            addr = self.mem.get(self.eip, 4)  # d32
            self.eip += 4
            addr = to_int(addr, True)
        else:
            addr = to_int(self.reg.get(RM, 4), True)
            
        if MOD == 0b01:
            d8 = self.mem.get(self.eip, 1)
            self.eip += 1
            
            addr += to_int(d8, True)
        elif MOD == 0b10:
            d32 = self.mem.get(self.eip, 4) 
            self.eip += 4
            
            addr += to_int(d32, True)
    else:  # there's a SIB
        SIB = self.mem.get(self.eip, 1)[0]
        self.eip += 1

        base  = SIB & 0b111; SIB >>= 3
        index = SIB & 0b111; SIB >>= 3
        scale = SIB
        
        if MOD == 0b01:
            d8 = self.mem.get(self.eip, 1)
            self.eip += 1
                
            addr = to_int(d8, True)
        elif MOD == 0b10:
            d32 = self.mem.get(self.eip, 4) 
            self.eip += 4
            
            addr = to_int(d32, True)
        else:
            addr = 0
        
        if index != 0b100:
            addr += to_int(self.reg.get(index, 4), True) << scale
            
        if base != 0b101:
            addr += to_int(self.reg.get(base, 4), True)
        else:
            if MOD == 0b00:
                d32 = self.mem.get(self.eip, 4) 
                self.eip += 4
            
                addr += to_int(d32, True)
            else:
                addr += to_int(self.reg.get(base, 4), True)
                
                if MOD == 0b01:
                    d8 = self.mem.get(self.eip, 1)
                    self.eip += 1
                
                    addr += to_int(d8, True)
                elif MOD == 0b10:
                    d32 = self.mem.get(self.eip, 4) 
                    self.eip += 4
            
                    addr += to_int(d32, True)
                    
    return (1, addr, size1), (0, REG, size2)


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
