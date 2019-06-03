import ctypes

from .ctypes_types import ubyte, uword, udword

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

class _Eflags_bits(ctypes.LittleEndianStructure):
    _fields_ = [
        ('CF', ubyte, 1),
        ('_', ubyte, 1),
        ('PF', ubyte, 1),
        ('_', ubyte, 1),
        ('AF', ubyte, 1),
        ('_', ubyte, 1),
        ('ZF', ubyte, 1),
        ('SF', ubyte, 1),
        ('TF', ubyte, 1),
        ('IF', ubyte, 1),
        ('DF', ubyte, 1),
        ('OF', ubyte, 1),
    ]

class _Eflags(ctypes.Union):
    _anonymous_ = '__bits',
    _fields_ = [
        ('eflags', uword),
        ('__bits', _Eflags_bits)
    ]


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
               ] + [
        ('eflags', _Eflags)
    ]

    del a, b


class _sreg_hidden(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('base', udword),
        ('limit', udword),
        ('access', udword)
    ]

    def __str__(self):
        return f'base=0x{self.base:08x}, limit=0x{self.limit:08x}, access={self.access:08x}'

class _one_sreg(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('visible', udword),
        ('hidden', _sreg_hidden)
    ]

    def __str__(self):
        return f'Sreg(visible=0x{self.visible:08x}, {self.hidden})'

class SegmentDescriptor(ctypes.LittleEndianStructure):
    _fields_ = [
        ('base_3', ubyte),
        ('G', ubyte, 1),
        ('DB', ubyte, 1),
        ('L', ubyte, 1),
        ('AVL', ubyte, 1),
        ('limit_2', ubyte, 4),
        ('P', ubyte, 1),
        ('DPL', ubyte, 2),
        ('S', ubyte, 1),
        ('type', ubyte, 4),
        ('base_2', ubyte),

        ('base_1', uword),
        ('limit_1', uword)
    ]

class Sreg(ctypes.Structure):
    """
    Segment registers.
    """
    _pack_ = 1
    _fields_ = [
        (name, _one_sreg)
        for name in 'ES CS SS DS FS GS'.split()
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__names = 'ES CS SS DS FS GS'.split()
        self.__ptr = ctypes.cast(ctypes.pointer(self), ctypes.POINTER(_one_sreg))

    def set(self, offset: int, segment_selector: int, descriptor_data: bytes) -> None:
        index, TI, RPL = segment_selector >> 3, (segment_selector >> 2) & 1, segment_selector & 0b11
        #print(f'offset={offset:03b}, (index={index:05b}, TI={TI:1b}, RPL={RPL:02b}), descriptor: {descriptor_data}')

        descriptor = SegmentDescriptor.from_buffer_copy(descriptor_data)

        # TODO: handle priviledge level

        self.__ptr[offset].visible = segment_selector
        self.__ptr[offset].hidden.base = (descriptor.base_3 << 23) | (descriptor.base_2 << 15) | descriptor.base_1
        self.__ptr[offset].hidden.limit = (descriptor.limit_2 << 15) | descriptor.limit_1

        print(self.__ptr[offset])

    def get(self, offset: int) -> _one_sreg:
        assert 0b000 <= offset <= 0b101

        return self.__ptr[offset]


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

    def set(self, offset: int, size: int, value: int) -> None:
        if size == 4:
            self.__ptr32[offset] = value
        elif size == 2:
            self.__ptr16[2 * offset] = value
        elif size == 1:
            self.__ptr8[4 * (offset % 4) + offset // 4] = value
        else:
            raise ValueError(f'Reg32.set_val(offset={offset}, size={size}, value={value}): unexpected size: {size}')

    def set4(self, offset: int, value: int):
        self.__ptr32[offset] = value
