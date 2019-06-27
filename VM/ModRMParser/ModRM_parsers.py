from enum import IntFlag
from collections import namedtuple as n

from ..Memory import Memory
from ..Registers import Reg32


class AddressC(IntFlag):
    invalid = 0
    base = 1
    index = 0b10
    index_scale = 0b100
    disp8 = 0b1000
    disp32 = 0b10000
    register = 0b100000


attributes = 'base index scale off right'
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

Operands = n('operands', 'RM R')
Address = n('address', 'hardware address')

class Address(n('address', 'hardware address')):
    def str(self, size: int) -> str: 
        if isinstance(self.hardware, Memory):
            return f'[0x{self.address:08x}]'
        return reg_names[self.address][size]


def to_int(bytecode: bytes) -> int:
    return int.from_bytes(bytecode, 'little', signed=True)


class Reg(n('Register', attributes)):
    _type = AddressC.register

    def parse_raw(self, bytecode: bytes) -> (str, str):
        return reg_names[self.base], reg_names[self.right]
        
    def address(self, cpu) -> tuple:
        cpu.eip += self.off
        
        return (
            (cpu.reg, self.base),
            (cpu.reg, self.right)
        )


class Base(n('Base', attributes)):
    _type = AddressC.base

    def parse_raw(self, bytecode: bytes) -> (str, str):
        return f'[{reg_names[self.base]}]', reg_names[self.right]
        
    def address(self, cpu) -> tuple:
        Base = cpu.reg.get(self.base, 4, True)
        cpu.eip += self.off
        
        return (
            (cpu.mem, Base),
            (cpu.reg, self.right)
        )


class BI(n('BaseIndex', attributes)):
    _type = AddressC.base | AddressC.index

    def parse_raw(self, bytecode: bytes) -> (str, str):
        return f'[{reg_names[self.base]} + {reg_names[self.index]}]', reg_names[self.right]
        
    def address(self, cpu) -> tuple:
        Base = cpu.reg.get(self.base, 4, True)
        Index = cpu.reg.get(self.index, 4, True)
        cpu.eip += self.off
        
        return (
            (cpu.mem, Base + Index),
            (cpu.reg, self.right)
        )


class BIS(n('BaseIndexScale', attributes)):
    _type = AddressC.base | AddressC.index_scale

    def parse_raw(self, bytecode: bytes) -> (str, str):
        return f'[{reg_names[self.base]} + {reg_names[self.index]}*{self.scale}]', reg_names[self.right]
        
    def address(self, cpu) -> tuple:
        Base = cpu.reg.get(self.base, 4, True)
        Index = cpu.reg.get(self.index, 4, True)
        cpu.eip += self.off
        
        return (
            (cpu.mem, Base + Index * self.scale),
            (cpu.reg, self.right)
        )


class BD8(n('BaseDisp8', attributes)):
    _type = AddressC.base | AddressC.disp8

    def parse_raw(self, bytecode: bytes) -> (str, str):
        d8 = to_int(bytecode[self.off:self.off + 1])

        return f'[{reg_names[self.base]} + 0x{d8:01x}]', reg_names[self.right]
        
    def address(self, cpu) -> tuple:
        Base = cpu.reg.get(self.base, 4, True)
        d8 = cpu.mem.get_eip(cpu.eip + self.off, 1, True)
        cpu.eip += self.off + 1
        
        return (
            (cpu.mem, Base + d8),
            (cpu.reg, self.right)
        )


class BID8(n('BaseIndexDisp8', attributes)):
    _type = AddressC.base | AddressC.index | AddressC.disp8

    def parse_raw(self, bytecode: bytes) -> (str, str):
        d8 = to_int(bytecode[self.off:self.off + 1])

        return f'[{reg_names[self.base]} + {reg_names[self.index]} + 0x{d8:01x}]', reg_names[self.right]
        
    def address(self, cpu) -> tuple:
        Base = cpu.reg.get(self.base, 4, True)
        Index = cpu.reg.get(self.index, 4, True)
        d8 = cpu.mem.get_eip(cpu.eip + self.off, 1, True)
        cpu.eip += self.off + 1
        
        return (
            (cpu.mem, Base + Index + d8),
            (cpu.reg, self.right)
        )


class BISD8(n('BaseIndexScaleDisp8', attributes)):
    _type = AddressC.base | AddressC.index_scale | AddressC.disp8

    def parse_raw(self, bytecode: bytes) -> (str, str):
        d8 = to_int(bytecode[self.off:self.off + 1])

        return f'[{reg_names[self.base]} + {reg_names[self.index]}*{self.scale} + 0x{d8:01x}]', reg_names[self.right]
        
    def address(self, cpu) -> tuple:
        Base = cpu.reg.get(self.base, 4, True)
        Index = cpu.reg.get(self.index, 4, True)
        d8 = cpu.mem.get(cpu.eip + self.off, 1, True)
        cpu.eip += self.off + 1
        
        return (
            (cpu.mem, Base + Index * self.scale + d8),
            (cpu.reg, self.right)
        )


class D32(n('Disp32', attributes)):
    _type = AddressC.disp32

    def parse_raw(self, bytecode: bytes) -> (str, str):
        d32 = to_int(bytecode[self.off:self.off + 4])

        return f'[0x{d32:08x}]', reg_names[self.right]
        
    def address(self, cpu) -> tuple:
        d32 = cpu.mem.get(cpu.eip + self.off, 4, True)
        cpu.eip += self.off + 4
        
        return (
            (cpu.mem, d32),
            (cpu.reg, self.right)
        )


class BD32(n('BaseDisp32', attributes)):
    _type = AddressC.base | AddressC.disp32

    def parse_raw(self, bytecode: bytes) -> (str, str):
        d32 = to_int(bytecode[self.off:self.off + 4])

        return f'[{reg_names[self.base]} + 0x{d32:08x}]', reg_names[self.right]
        
    def address(self, cpu) -> tuple:
        Base = cpu.reg.get(self.base, 4, True)
        d32 = cpu.mem.get(cpu.eip + self.off, 4, True)
        cpu.eip += self.off + 4
        
        return (
            (cpu.mem, Base + d32),
            (cpu.reg, self.right)
        )


class BID32(n('BaseIndesDisp32', attributes)):
    _type = AddressC.base | AddressC.index | AddressC.disp32

    def parse_raw(self, bytecode: bytes) -> (str, str):
        d32 = to_int(bytecode[self.off:self.off + 4])

        return f'[{reg_names[self.base]} + {reg_names[self.index]} + 0x{d32:08x}]', reg_names[self.right]
        
    def address(self, cpu) -> tuple:
        Base = cpu.reg.get(self.base, 4, True)
        Index = cpu.reg.get(self.index, 4, True)
        d32 = cpu.mem.get(cpu.eip + self.off, 4, True)
        cpu.eip += self.off + 4
        
        return (
            (cpu.mem, Base + Index + d32),
            (cpu.reg, self.right)
        )


class ISD32(n('IndexScaleDisp32', attributes)):
    _type = AddressC.index_scale | AddressC.disp32

    def parse_raw(self, bytecode: bytes) -> (str, str):
        d32 = to_int(bytecode[self.off:self.off + 4])

        return f'[{reg_names[self.index]}*{self.scale} + 0x{d32:08x}]', reg_names[self.right]
        
    def address(self, cpu) -> tuple:
        Index = cpu.reg.get(self.index, 4, True)
        d32 = cpu.mem.get(cpu.eip + self.off, 4, True)
        cpu.eip += self.off + 4
        
        return (
            (cpu.mem, Index * self.scale + d32),
            (cpu.reg, self.right)
        )


class BISD32(n('BaseIndexScaleDisp32', attributes)):
    _type = AddressC.base | AddressC.index_scale | AddressC.disp32

    def parse_raw(self, bytecode: bytes) -> (str, str):
        d32 = to_int(bytecode[self.off:self.off + 4])

        return f'[{reg_names[self.base]} + {reg_names[self.index]}*{self.scale} + 0x{d32:08x}]', reg_names[self.right]
        
    def address(self, cpu) -> tuple:
        Base = cpu.reg.get(self.base, 4, True)
        Index = cpu.reg.get(self.index, 4, True)
        d32 = cpu.mem.get(cpu.eip + self.off, 4, True)
        cpu.eip += self.off + 4
        
        return (
            (cpu.mem, Base + Index * self.scale + d32),
            (cpu.reg, self.right)
        )


class_map = {
    cls._type: cls
    for name, cls in globals().items()
    if hasattr(cls, '_type')
}
