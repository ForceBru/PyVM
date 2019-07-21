import ctypes

if __name__ == '__main__':
    from ctypes_types import ubyte, uword, udword, uqword, dbl, flt
else:
    from .ctypes_types import ubyte, uword, udword, uqword, dbl, flt


class _FPU_status(ctypes.LittleEndianStructure):
    """
    See: Vol.1 Section 8.1.3 (fig. 8-4 x87 FPU Status Word)
    """
    _pack_ = 1
    _fields_ = [
        ('B',   uword, 1),  # FPU busy
        ('C3',  uword, 1),  # Code[3]
        ('TOP', uword, 3),  # Top of stack pointer
        ('C2',  uword, 1),  # Code[2]
        ('C1',  uword, 1),  # Code[1]
        ('C0',  uword, 1),  # Code[0]

        ('ES',  uword, 1),  # Exception summary status
        ('SF',  uword, 1),  # Stack fault
                        # Exception flags:
        ('PE',  uword, 1),  # Precision
        ('UE',  uword, 1),  # Underflow
        ('OE',  uword, 1),  # Overflow
        ('ZE',  uword, 1),  # Zero divide
        ('DE',  uword, 1),  # Denormalized operand
        ('IE',  uword, 1),  # Invalid operation
    ][::-1]


class _FPU_control(ctypes.LittleEndianStructure):
    """
    See: Vol. 1 Section 8.1.5 (fig. 8-6 x87 FPU Control Word)
    """
    _pack_ = 1
    _fields_ = [
        ('__reserved', uword, 3),

        ('x', uword, 1),  # Infinity control
        ('RC', uword, 2),  # Rounding control
        ('PC', uword, 2),  # Precision control

        ('__reserved', uword, 2),
                        # Exception masks:
        ('PM', uword, 1),  # Precision
        ('UM', uword, 1),  # Underflow
        ('OM', uword, 1),  # Overflow
        ('ZM', uword, 1),  # Zero divide
        ('DM', uword, 1),  # Denormal operand
        ('IM', uword, 1),  # Invalid operand
    ][::-1]


class FPU_status(ctypes.Union):
    _pack_ = 1
    _anonymous_ = '__status',
    _fields_ = [
        ('value', uword),
        ('__status', _FPU_status)
    ]


class FPU_control(ctypes.Union):
    _pack_ = 1
    _anonymous_ = '__control',
    _fields_ = [
        ('value', uword),
        ('__control', _FPU_control)
    ]


class FPU_tag(ctypes.LittleEndianStructure):
    ...  # TODO: FPU tag word


class binary32(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('sign', udword, 1),
        ('exponent', udword, 8),
        ('significand', udword, 23)
    ][::-1]

    BIAS = 127

    def __float__(self):
        return flt.from_buffer(self).value


class binary64(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('sign', uqword, 1),
        ('exponent', uqword, 11),
        ('significand', uqword, 52)
    ][::-1]

    BIAS = 1023

    def __float__(self):
        return dbl.from_buffer(self).value


class _binary80(ctypes.LittleEndianStructure):  # Double Extended-Precision Floating-Point format
    _pack_ = 1
    _fields_ = [
        ('sign', uword, 1),
        ('exponent', uword, 15),
        ('significand', uqword)
    ][::-1]

    BIAS = 16383


class FPInvalidArithmeticOperand(Exception):
    ...


class binary80(_binary80):
    ZERO = lambda sign=0: binary80(0, 0, sign)
    SNaN = lambda: binary80(  # Signaling Not a Number
        (0b10 << 62) + 1,
        0b111111111111111,
        0
    )
    QNaN = lambda: binary80(  # Quiet Not a Number
        (0b11 << 62) + 1,
        0b111111111111111,
        0
    )
    FPIn = lambda: binary80(  # Floating-point indefinite (result of invalid calculations, like sqrt(-1))
        (0b11 << 62),
        0b111111111111111,
        0
    )
    Inf  = lambda sign=0: binary80(  # Infinity
        (0b10 << 62),
        0b111111111111111,
        sign
    )

    def __str__(self):
        return f'{float(self):+.016f}'

    def __float__(self) -> float:
        if self.exponent == 0:
            if self.significand == 0:
                return 0.0

        true_exponent = self.exponent - self.BIAS
        significand = self.significand >> 11

        return float(binary64(significand, true_exponent + 1023, self.sign))

    def __int__(self) -> int:
        return int(float(self))

    def __align_exponents(self, other) -> (int, int, int):
        """
        Align the exponents of two `binary80` floating-point numbers (`a` and `b`).
        :param a: First double-extended precision floating point number.
        :param b: Second double-extended precision floating point number.
        :return: Tuple: exponent, adjusted_significand_a, adjusted_significand_b
        """

        s1, s2 = self.significand, other.significand
        e1, e2 = self.exponent, other.exponent

        d = e1 - e2

        if d >= 0:
            s2 >>= d
            exponent = e1
        else:
            s1 >>= -d
            exponent = e2

        return exponent, s1, s2

    @staticmethod
    def __normalize(exponent: int, significand: int, bits: int = 63) -> (int, int):
        """
        Normalize the significand, if necessary. A normalized significand is in the form: 1.xxxxxxxxx
        :param exponent:
        :param significand:
        :param bits: The number of bits after the decimal point. The number of `x` in `1.xxxx`.
        :return: Exponent, normalized significand
        """

        if (significand >> bits) > 1:
            # If the number before the decimal point is 0b10 or 0b11
            significand >>= 1
            exponent += 1

        while significand != 0 and (significand >> bits) == 0:
            # The digit before the decimal point must not be zero
            significand <<= 1
            exponent -= 1

        return exponent, significand

    def __is_zero(self) -> bool:
        return self.exponent == 0 and self.significand == 0

    def __is_SNaN(self) -> bool:
        return self.exponent == 0b111111111111111 and\
               (self.significand & ((1 << 62) - 1) != 0) and\
               (self.significand >> 62) == 0b10

    def __is_QNaN(self) -> bool:
        return self.exponent == 0b111111111111111 and \
               (self.significand >> 62) == 0b11

    def __is_NaN(self) -> bool:
        return self.__is_SNaN() or self.__is_QNaN()

    def __is_Inf(self, sign=None) -> bool:
        """
        Is infinity?
        :return:
        """
        if sign is None:
            return self.exponent == 0b111111111111111 and\
                   (self.significand >> 62) == 0b10 and\
                   (self.significand & ((1 << 62) - 1) == 0)
        return self.exponent == 0b111111111111111 and \
               (self.significand >> 62) == 0b10 and \
               (self.significand & ((1 << 62) - 1) == 0) and self.sign == sign

    def __neg__(self):
        return binary80(self.significand, self.exponent, not self.sign)

    def __add__(self, other):
        if self.sign and not other.sign:
            return other - (-self)
        if not self.sign and other.sign:
            return self - (-other)

        sign = self.sign

        exponent, s1, s2 = self.__align_exponents(other)

        S = s1 + s2

        exponent, S = binary80.__normalize(exponent, S)

        return binary80(S, exponent, sign)

    def __sub__(self, other):
        if self.sign:
            if other.sign:
                return -other - -self
            return -(-self + other)
        else:
            if other.sign:
                return self + -other

        exponent, s1, s2 = self.__align_exponents(other)

        S = s1 - s2

        if S > 0:
            sign = 0
        elif S < 0:
            sign = 1
            S = -S
        else:
            return binary80.ZERO()

        exponent, S = binary80.__normalize(exponent, S)

        return binary80(S, exponent, sign)

    def __mul__(self, other):
        if self.__is_zero() or other.__is_zero():
            return binary80.ZERO()

        sign = self.sign ^ other.sign

        s1, s2 = self.significand, other.significand
        e1, e2 = self.exponent, other.exponent

        exponent = e1 + e2 - self.BIAS

        S = s1 * s2

        exponent, S = binary80.__normalize(exponent, S, 63 * 2)

        S >>= 63  # multiplication gave 63 more bits, get rid of them

        return binary80(S, exponent, sign)

    def __truediv__(self, other):
        if self.__is_NaN() or other.__is_NaN():
            return binary80.SNaN()

        sign = self.sign ^ other.sign
        if self.__is_Inf():
            if other.__is_Inf():
                raise FPInvalidArithmeticOperand()
            return binary80.Inf(sign)
        elif self.__is_zero():
            if other.__is_zero():
                raise FPInvalidArithmeticOperand()
            return binary80.ZERO(sign)
        elif other.__is_zero():
            raise FPInvalidArithmeticOperand()

        s1, s2 = self.significand, other.significand
        e1, e2 = self.exponent, other.exponent

        exponent = e1 - e2 + self.BIAS

        S = s1 // s2
        S <<= 63

        exponent, S = binary80.__normalize(exponent, S)

        return binary80(S, exponent, sign)

    def __eq__(self, other) -> bool:
        if self.__is_NaN() or other.__is_NaN():
            return False

        if self.__is_zero() and other.__is_zero():
            return True

        return self.sign == other.sign\
               and self.exponent == other.exponent\
               and self.significand == other.significand

    def __gt__(self, other) -> bool:
        if self.__is_NaN() or other.__is_NaN():
            return False
        if self.__is_Inf(0):
            # positive infinity
            return True
        if self.__is_Inf(1):
            # negative infinity
            return False

        if not self.sign:
            if other.sign:
                # (positive) > (negative)
                return True
            if self.exponent > other.exponent:
                return True

            return self.significand > other.significand

        if not other.sign:
            # (negative) < (positive)
            return False
        if self.exponent < other.exponent:
            return True
        return self.significand < other.significand

    def __lt__(self, other) -> bool:
        if self.__is_NaN() or other.__is_NaN():
            return False
        if self.__is_Inf(0):
            # positive infinity
            return False
        if self.__is_Inf(1):
            # negative infinity
            return True

        if not self.sign:
            if other.sign:
                # (positive) > (negative)
                return False
            # (positive) vs (positive)
            if self.exponent < other.exponent:
                return True

            return self.significand < other.significand

        # (negative) vs (something else)
        if not other.sign:
            # (negative) < (positive)
            return True
        # (negative) vs (negative)
        if self.exponent < other.exponent:
            return False
        return self.significand > other.significand

    @staticmethod
    def from_int(val: int):
        return binary80.from_double(float(val))  # TODO: this is a placeholder

    @staticmethod
    def from_double(val: float):
        double = binary64.from_buffer_copy(dbl(val))

        return binary80(
            (double.significand << (63 - 52)) | (1 << 63),
            double.exponent - binary64.BIAS + binary80.BIAS,
            double.sign
        )

    @staticmethod
    def from_float(val: float):
        _float = binary32.from_buffer_copy(flt(val))

        return binary80(
            (_float.significand << (63 - 23)) | (1 << 63),
            _float.exponent - binary32.BIAS + binary80.BIAS,
            _float.sign
        )


class _FPU(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        # Control registers
        ('control', FPU_control),
        ('status', FPU_status),
        ('tag', FPU_tag),

        ('LIP', uqword, 48),  # Last Instruction Pointer (FCS:FIP)
        ('LDP', uqword, 48),  # Last Data Pointer (FDS:FDP)
        ('FOP', uword, 11),   # Opcode of the last x87 non-control instruction executed that
                              # incurred and unmasked x87 exception

        # Data registers
        ('reg', (binary80 * 8)),
    ][::-1]


class FPU(_FPU):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.status.TOP = 0  # the stack is empty

    def store_top(self, value: binary80) -> None:
        self.reg[self.status.TOP] = value

    def store(self, index: int, value: binary80) -> None:
        self.reg[self.status.TOP + index] = value

    def push(self, value: binary80) -> None:
        self.status.TOP -= 1
        self.status.C1 = self.status.TOP == 7  # set to 1 if stack overflow occurred

        self.reg[self.status.TOP] = value

    def _push_float(self, value: float) -> None:
        self.status.TOP -= 1
        self.reg[self.status.TOP] = binary80.from_float(value)

    def pop(self) -> binary80:
        retval = self.reg[self.status.TOP]
        self.status.TOP += 1

        self.status.C1 = self.status.TOP != 0  # set to 0 if stack overflow occurred

        return retval

    def _pop_float(self) -> float:
        retval = self.reg[self.status.TOP]
        self.status.TOP += 1

        return float(retval)

    def add(self, a: int, b: int) -> binary80:
        res = self.ST(a) + self.ST(b)
        self.store(a, res)

        return res

    def sub(self, a: int, b: int) -> binary80:
        res = self.ST(a) - self.ST(b)
        self.store(a, res)

        return res

    def mul(self, a: int, b: int) -> binary80:
        res = self.ST(a) * self.ST(b)
        self.store(a, res)

        return res

    def div(self, a: int, b: int) -> binary80:
        res = self.ST(a) / self.ST(b)
        self.store(a, res)

        return res

    def ST(self, index: int) -> binary80:
        return self.reg[self.status.TOP + index]


if __name__ == '__main__':
    fpu = FPU()
    fpu._push_float(3.14)
    fpu._push_float(-3.14)
    for i in range(2):
        print(f'ST({i}) = {float(fpu.ST(i))}')

    fpu.add(0, 1)
    for i in range(2):
        print(f'ST({i}) = {float(fpu.ST(i))}')

    fpu.mul(0, 1)
    for i in range(2):
        print(f'ST({i}) = {float(fpu.ST(i))}')

    print(fpu._pop_float())
