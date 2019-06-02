import ctypes

from ctypes_types import ubyte, uword, udword

__all__ = 'Reg32',

REG_LETTERS = 'acdb'
REG_TAILS = 'sp', 'bp', 'si', 'di'


def GenRegX(letter: str):
    assert letter in REG_LETTERS

    class _HiLo_byte(ctypes.LittleEndianStructure):
        _pack_ = 1
        # these are SWAPPED because of endianness
        _fields_ = [
            (letter + 'l', ubyte),
            (letter + 'h', ubyte),
        ]

    # ctypes' docs (16.12.1.11. Structure/union alignment and byte order) say LittleEndianUnion exists, like LittleEndianStructure but it doesn't
    class _Reg32(ctypes.Union):
        _pack_ = 1
        _anonymous_ = '__byte',
        _fields_ = [
            (f'e{letter}x', udword),
            (letter + 'x', uword),
            ('__byte', _HiLo_byte)
        ]

    return _Reg32


def GenReg(tail: str):
    assert tail in REG_TAILS

    class _Reg32(ctypes.Union):
        _fields_ = [
            (f'e{tail}', udword),
            (tail, uword),
        ]

    return _Reg32


class _Reg32_base(ctypes.Structure):
    a = ['reg_' + l for l in REG_LETTERS]
    b = ['reg_' + t for t in REG_TAILS]

    _anonymous_ = tuple(a + b)

    _fields_ = [
                   (name, GenRegX(name[4:]))
                   for name in a
               ] + [
                   (name, GenReg(name[4:]))
                   for name in b
               ]

    del a, b


class Reg32(_Reg32_base):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        ptr = ctypes.pointer(self)

        self.__ptr8 = ctypes.cast(ptr, ctypes.POINTER(ubyte))
        self.__ptr16 = ctypes.cast(ptr, ctypes.POINTER(uword))
        self.__ptr32 = ctypes.cast(ptr, ctypes.POINTER(udword))

    def get(self, offset: int, size: int) -> int:
        if size == 4:
            return self.__ptr32[offset]
        elif size == 2:
            return self.__ptr16[2 * offset]
        elif size == 1:
            return self.__ptr8[4 * (offset % 4) + offset // 4]

        raise ValueError(f'Reg32.get(offset={offset}, size={size}): unexpected size: {size}')

    def set_val(self, offset: int, size: int, value: int) -> None:
        if size == 4:
            self.__ptr32[offset] = value
        elif size == 2:
            self.__ptr16[2 * offset] = value
        elif size == 1:
            self.__ptr8[4 * (offset % 4) + offset // 4] = value
        else:
            raise ValueError(f'Reg32.set_val(offset={offset}, size={size}, value={value}): unexpected size: {size}')

        return value