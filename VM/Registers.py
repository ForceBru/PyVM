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
    _pack_ = 1
    _fields_ = [
        ('CF', uword, 1),
        ('__', uword, 1),
        ('PF', uword, 1),
        ('__', uword, 1),
        ('AF', uword, 1),
        ('__', uword, 1),
        ('ZF', uword, 1),
        ('SF', uword, 1),
        ('TF', uword, 1),
        ('IF', uword, 1),
        ('DF', uword, 1),
        ('OF', uword, 1),
    ][::-1]


class _Eflags(ctypes.Union):
    _anonymous_ = '__bits',
    _fields_ = [
        ('eflags', uword),
        ('__bits', _Eflags_bits)
    ]


class _Reg32_base(ctypes.LittleEndianStructure):
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
    ][::-1]

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
    _pack_ = 1
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
    ][::-1]

    def __str__(self):
        return f'SegmentDescriptor(base3={self.base_3:08b}, G={self.G:1b}, DB={self.DB:1b}, L={self.L:1b}, \
AVL={self.AVL:1b}, limit2={self.limit_2:04b}, P={self.P:1b}, DPL={self.DPL:02b}, S={self.S:1b}, \
type={self.type:04b}, base2={self.base_2:08b}, base1={self.base_1:016b}, limit1={self.limit_1:016b})'


class Sreg(ctypes.LittleEndianStructure):
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
        # index, TI, RPL = segment_selector >> 3, (segment_selector >> 2) & 1, segment_selector & 0b11
        # print(f'offset={offset:03b}, (index={index:05b}, TI={TI:1b}, RPL={RPL:02b}), descriptor: {descriptor_data}')

        descriptor = SegmentDescriptor.from_buffer_copy(descriptor_data)

        # print(f'Descriptor: {descriptor}, descr. data=={descriptor_data}')

        # TODO: handle priviledge level

        self.__ptr[offset].visible = segment_selector
        self.__ptr[offset].hidden.base = (descriptor.base_3 << 24) | (descriptor.base_2 << 16) | descriptor.base_1
        self.__ptr[offset].hidden.limit = (descriptor.limit_2 << 16) | descriptor.limit_1

        # print(f'segment.visible={self.__ptr[offset].visible}, segment.hidden.base=0x{self.__ptr[offset].hidden.base:08x}, segment.hidden.limit=0x{self.__ptr[offset].hidden.limit:08x}')

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

    def get(self, offset: int, size: int, signed=False) -> int:
        if size == 4:
            if not signed:
                return self.__ptr32[offset]

            ret = self.__ptr32[offset]
            return ret if ret < 2147483648 else ret - 4294967296
        elif size == 2:
            if not signed:
                return self.__ptr16[2 * offset]

            ret = self.__ptr16[2 * offset]
            return ret if ret < 32768 else ret - 65536
        elif size == 1:
            if not signed:
                return self.__ptr8[4 * (offset % 4) + offset // 4]

            ret = self.__ptr8[4 * (offset % 4) + offset // 4]
            return ret if ret < 128 else ret - 256

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
