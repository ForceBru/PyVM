from .Memory import Memory
from .Registers import Reg32

reg_names = [
    [0, 'al', 'ax', 0, 'eax'],
    [0, 'cl', 'cx', 0, 'ecx'],
    [0, 'dl', 'dx', 0, 'edx'],
    [0, 'bl', 'bx', 0, 'ebx'],
    [0, 'ah', 'sp', 0, 'esp'],
    [0, 'ch', 'bp', 0, 'ebp'],
    [0, 'dh', 'si', 0, 'esi'],
    [0, 'bh', 'di', 0, 'edi'],
    ]
    
def debug_address(addr: tuple, size: int) -> str:
    hardware, addr = addr
    
    if isinstance(hardware, Reg32):
        return reg_names[addr][size]
        
    return f'0x{addr:08x}'
