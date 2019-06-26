from enum import IntFlag
from collections import namedtuple as n


class AddressC(IntFlag):
    invalid = 0
    base = 1
    index = 0b10
    index_scale = 0b100
    disp8 = 0b1000
    disp32 = 0b10000
    register = 0b100000


attributes = 'base index scale off right'
reg_names = 'eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi'


def to_int(bytecode: bytes) -> int:
    return int.from_bytes(bytecode, 'little', signed=True)


class Reg(n('Register', attributes)):
    _type = AddressC.register

    def parse_raw(self, bytecode: bytes) -> (str, str):
        return reg_names[self.base], reg_names[self.right]


class Base(n('Base', attributes)):
    _type = AddressC.base

    def parse_raw(self, bytecode: bytes) -> (str, str):
        return f'[{reg_names[self.base]}]', reg_names[self.right]


class BI(n('BaseIndex', attributes)):
    _type = AddressC.base | AddressC.index

    def parse_raw(self, bytecode: bytes) -> (str, str):
        return f'[{reg_names[self.base]} + {reg_names[self.index]}]', reg_names[self.right]


class BIS(n('BaseIndexScale', attributes)):
    _type = AddressC.base | AddressC.index_scale

    def parse_raw(self, bytecode: bytes) -> (str, str):
        return f'[{reg_names[self.base]} + {reg_names[self.index]}*{self.scale}]', reg_names[self.right]


class BD8(n('BaseDisp8', attributes)):
    _type = AddressC.base | AddressC.disp8

    def parse_raw(self, bytecode: bytes) -> (str, str):
        d8 = to_int(bytecode[self.off:self.off + 1])

        return f'[{reg_names[self.base]} + 0x{d8:01x}]', reg_names[self.right]


class BID8(n('BaseIndexDisp8', attributes)):
    _type = AddressC.base | AddressC.index | AddressC.disp8

    def parse_raw(self, bytecode: bytes) -> (str, str):
        d8 = to_int(bytecode[self.off:self.off + 1])

        return f'[{reg_names[self.base]} + {reg_names[self.index]} + 0x{d8:01x}]', reg_names[self.right]


class BISD8(n('BaseIndexScaleDisp8', attributes)):
    _type = AddressC.base | AddressC.index_scale | AddressC.disp8

    def parse_raw(self, bytecode: bytes) -> (str, str):
        d8 = to_int(bytecode[self.off:self.off + 1])

        return f'[{reg_names[self.base]} + {reg_names[self.index]}*{self.scale} + 0x{d8:01x}]', reg_names[self.right]


class D32(n('Disp32', attributes)):
    _type = AddressC.disp32

    def parse_raw(self, bytecode: bytes) -> (str, str):
        d32 = to_int(bytecode[self.off:self.off + 4])

        return f'[0x{d32:08x}]', reg_names[self.right]


class BD32(n('BaseDisp32', attributes)):
    _type = AddressC.base | AddressC.disp32

    def parse_raw(self, bytecode: bytes) -> (str, str):
        d32 = to_int(bytecode[self.off:self.off + 4])

        return f'[{reg_names[self.base]} + 0x{d32:08x}]', reg_names[self.right]


class BID32(n('BaseIndesDisp32', attributes)):
    _type = AddressC.base | AddressC.index | AddressC.disp32

    def parse_raw(self, bytecode: bytes) -> (str, str):
        d32 = to_int(bytecode[self.off:self.off + 4])

        return f'[{reg_names[self.base]} + {reg_names[self.index]} + 0x{d32:08x}]', reg_names[self.right]


class ISD32(n('IndexScaleDisp32', attributes)):
    _type = AddressC.index_scale | AddressC.disp32

    def parse_raw(self, bytecode: bytes) -> (str, str):
        d32 = to_int(bytecode[self.off:self.off + 4])

        return f'[{reg_names[self.index]}*{self.scale} + 0x{d32:08x}]', reg_names[self.right]


class BISD32(n('BaseIndexScaleDisp32', attributes)):
    _type = AddressC.base | AddressC.index_scale | AddressC.disp32

    def parse_raw(self, bytecode: bytes) -> (str, str):
        d32 = to_int(bytecode[self.off:self.off + 4])

        return f'[{reg_names[self.base]} + {reg_names[self.index]}*{self.scale} + 0x{d32:08x}]', reg_names[self.right]


class_map = {
    cls._type: cls
    for name, cls in globals().items()
    if hasattr(cls, '_type')
}