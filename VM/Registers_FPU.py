import ctypes

from ctypes_types import ubyte, uword, udword, uqword


class _FPU_status(ctypes.LittleEndianStructure):
    """
    See: Vol.1 Section 8.1.3 (fig. 8-4 x87 FPU Status Word)
    """
    _pack_ = 1
    _fields_ = [
        ('B',   ubyte, 1),  # FPU busy
        ('C3',  ubyte, 1),  # Code[3]
        ('TOP', ubyte, 3),  # Top of stack pointer
        ('C2',  ubyte, 1),  # Code[2]
        ('C1',  ubyte, 1),  # Code[1]
        ('C0',  ubyte, 1),  # Code[0]

        ('ES',  ubyte, 1),  # Exception summary status
        ('SF',  ubyte, 1),  # Stack fault
                        # Exception flags:
        ('PE',  ubyte, 1),  # Precision
        ('UE',  ubyte, 1),  # Underflow
        ('OE',  ubyte, 1),  # Overflow
        ('ZE',  ubyte, 1),  # Zero divide
        ('DE',  ubyte, 1),  # Denormalized operand
        ('IE',  ubyte, 1),  # Invalid operation
    ]


class _FPU_control(ctypes.LittleEndianStructure):
    """
    See: Vol. 1 Section 8.1.5 (fig. 8-6 x87 FPU Control Word)
    """
    _pack_ = 1
    _fields_ = [
        ('__reserved', ubyte, 3),

        ('x', ubyte, 1),  # Infinity control
        ('RC', ubyte, 2),  # Rounding control
        ('PC', ubyte, 2),  # Precision control

        ('__reserved', ubyte, 2),
                        # Exception masks:
        ('PM', ubyte, 1),  # Precision
        ('UM', ubyte, 1),  # Underflow
        ('OM', ubyte, 1),  # Overflow
        ('ZM', ubyte, 1),  # Zero divide
        ('DM', ubyte, 1),  # Denormal operand
        ('IM', ubyte, 1),  # Invalid operand
    ]


class FPU_status(ctypes.Union):
    _pack_ = 1
    _anonymous_ = '__status',
    _fields_ = [
        ('status', uword),
        ('__status', _FPU_status)
    ]


class FPU_control(ctypes.Union):
    _pack_ = 1
    _anonymous_ = '__control',
    _fields_ = [
        ('control', uword),
        ('__control', _FPU_control)
    ]


class FPU_tag(ctypes.LittleEndianStructure):
    ...  # TODO: FPU tag word


class _FPU_DEPFP(ctypes.LittleEndianStructure):  # Double Extended-Precision Floating-Point format
    _pack_ = 1
    _fields_ = [
        ('sign', ubyte, 1),
        ('exponent', uword, 15),
        ('significand', udword)
    ]


class _FPU(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        # Data registers
        ('R7', _FPU_DEPFP),
        ('R6', _FPU_DEPFP),
        ('R5', _FPU_DEPFP),
        ('R4', _FPU_DEPFP),
        ('R3', _FPU_DEPFP),
        ('R2', _FPU_DEPFP),
        ('R1', _FPU_DEPFP),
        ('R0', _FPU_DEPFP),

        # Control registers
        ('control', FPU_control),
        ('status', FPU_status),
        ('tag', FPU_tag),

        ('LIP', uqword, 48),  # Last Instruction Pointer (FCS:FIP)
        ('LDP', uqword, 48),  # Last Data Pointer (FDS:FDP)
        ('opcode', uword, 11)
    ]


class FPU(_FPU):
    def push(self, value: float) -> None:
        return NotImplemented

    def pop(self) -> float:
        return NotImplemented

    def ST(self, index: int) -> float:
        return NotImplemented


if __name__ == '__main__':
    fpu = FPU()
