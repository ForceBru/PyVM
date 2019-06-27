from ..util import Instruction, is_signed_out_of_range
from ..misc import parity, Shift, MSB, LSB

from functools import partialmethod as P
import operator

if __debug__:
    from ..debug import debug_operand, debug_register_operand
    import logging
    logger = logging.getLogger(__name__)

MAXVALS = [None, (1 << 8) - 1, (1 << 16) - 1, None, (1 << 32) - 1]  # MAXVALS[n] is the maximum value of an unsigned n-bit number
SIGNS   = [None, 1 << 8 - 1, 1 << 16 - 1, None, 1 << 32 - 1]  # SIGNS[n] is the maximum absolute value of a signed n-bit number


####################
# AND / OR / XOR / TEST
####################
class BITWISE(Instruction):
    """
    Perform a bitwise operation.
    Flags:
        OF, CF cleared
        SF, ZF, PF set according to the result
        AF undefined

    Operation: c <- a [op] b

    :param test: whether the instruction to be executed is TEST
    """

    def __init__(self):
        self.opcodes = {
            # AND
            0x24: P(self.r_imm, _8bit=True, operation=operator.and_),
            0x25: P(self.r_imm, _8bit=False, operation=operator.and_),

            0x80: [
                P(self.rm_imm, _8bit=True, _8bit_imm=True, operation=operator.and_, test=False, REG=4),  # AND r/m8, imm8
                P(self.rm_imm, _8bit=True, _8bit_imm=True, operation=operator.or_, test=False, REG=1),  # OR r/m8, imm8
                P(self.rm_imm, _8bit=True, _8bit_imm=True, operation=operator.xor, test=False, REG=6),  # XOR r/m8, imm8
                ],
            0x81: [
                P(self.rm_imm, _8bit=False, _8bit_imm=False, operation=operator.and_, test=False, REG=4),  # AND r/m, imm
                P(self.rm_imm, _8bit=False, _8bit_imm=False, operation=operator.or_, test=False, REG=1),  # OR r/m, imm
                P(self.rm_imm, _8bit=False, _8bit_imm=False, operation=operator.xor, test=False, REG=6),  # XOR r/m, imm
                ],
            0x83: [
                P(self.rm_imm, _8bit=False, _8bit_imm=True, operation=operator.and_, test=False, REG=4),  # AND r/m, imm8
                P(self.rm_imm, _8bit=False, _8bit_imm=True, operation=operator.or_, test=False, REG=1),  # OR r/m, imm8
                P(self.rm_imm, _8bit=False, _8bit_imm=True, operation=operator.xor, test=False, REG=6)  # XOR r/m, imm8
                ],

            0x20: P(self.rm_r, _8bit=True, operation=operator.and_),
            0x21: P(self.rm_r, _8bit=False, operation=operator.and_),

            0x22: P(self.r_rm, _8bit=True, operation=operator.and_),
            0x23: P(self.r_rm, _8bit=False, operation=operator.and_),

            # OR
            0x0C: P(self.r_imm, _8bit=True, operation=operator.or_),
            0x0D: P(self.r_imm, _8bit=False, operation=operator.or_),

            0x08: P(self.rm_r, _8bit=True, operation=operator.or_),
            0x09: P(self.rm_r, _8bit=False, operation=operator.or_),

            0x0A: P(self.r_rm, _8bit=True, operation=operator.or_),
            0x0B: P(self.r_rm, _8bit=False, operation=operator.or_),

            # XOR
            0x34: P(self.r_imm, _8bit=True, operation=operator.xor),
            0x35: P(self.r_imm, _8bit=False, operation=operator.xor),

            0x30: P(self.rm_r, _8bit=True, operation=operator.xor),
            0x31: P(self.rm_r, _8bit=False, operation=operator.xor),

            0x32: P(self.r_rm, _8bit=True, operation=operator.xor),
            0x33: P(self.r_rm, _8bit=False, operation=operator.xor),

            # TEST
            0xA8: P(self.r_imm, _8bit=True, operation=operator.and_, test=True),
            0xA9: P(self.r_imm, _8bit=False, operation=operator.and_, test=True),

            0xF6: P(self.rm_imm, _8bit=True, _8bit_imm=True, operation=operator.and_, test=True, REG=0),  # TEST r/m8, imm8
            0xF7: P(self.rm_imm, _8bit=False, _8bit_imm=False, operation=operator.and_, test=True, REG=0),  # TEST r/m, r/m

            0x84: P(self.rm_r, _8bit=True, operation=operator.and_, test=True),
            0x85: P(self.rm_r, _8bit=False, operation=operator.and_, test=True),
            }

    def r_imm(vm, _8bit, operation, test=False) -> True:
        sz = 1 if _8bit else vm.operand_size
        b = vm.mem.get(vm.eip, sz)
        vm.eip += sz

        a = vm.reg.get(0, sz)

        vm.reg.eflags.OF = vm.reg.eflags.CF = 0

        c = operation(a, b)

        vm.reg.eflags.SF = (c >> (sz * 8 - 1)) & 1

        c &= MAXVALS[sz]

        vm.reg.eflags.ZF = c == 0

        vm.reg.eflags.PF = parity(c & 0xFF)

        if not test:
            if __debug__:
                name = operation.__name__
            vm.reg.set(0, sz, c)
        else:
            if __debug__:
                name = 'test'

        if __debug__:
            logger.debug('%s %s=%d, imm%d=%d', name, debug_register_operand(0, sz), a, sz * 8, b)

        return True

    def rm_imm(vm, _8bit, _8bit_imm, operation, test: bool, REG: int) -> bool:
        ModRM = vm.mem.get_eip(vm.eip, 1)
        _REG = (ModRM & 0b00111000) >> 3

        if _REG != REG:
            return False

        sz = 1 if _8bit else vm.operand_size
        imm_sz = 1 if _8bit_imm else vm.operand_size

        RM, R = vm.process_ModRM()
        type, loc = RM

        b = vm.mem.get(vm.eip, imm_sz, True)
        vm.eip += imm_sz

        vm.reg.eflags.OF = vm.reg.eflags.CF = 0

        a = type.get(loc, sz)
        c = operation(a, b)

        vm.reg.eflags.SF = (c >> (sz * 8 - 1)) & 1

        c &= MAXVALS[sz]

        vm.reg.eflags.ZF = c == 0
        vm.reg.eflags.PF = parity(c)

        if not test:
            if __debug__:
                name = operation.__name__
            type.set(loc, sz, c)
        else:
            if __debug__:
                name = 'test'

        if __debug__:
            logger.debug('%s %s=%d, imm%d=%d', name, debug_operand(RM, sz), a, sz * 8, b)

        return True

    def rm_r(vm, _8bit, operation, test=False) -> True:
        sz = 1 if _8bit else vm.operand_size
        RM, R = vm.process_ModRM()
        type, loc = RM

        vm.reg.eflags.OF = vm.reg.eflags.CF = 0

        a = type.get(loc, sz)
        b = vm.reg.get(R[1], sz)

        c = operation(a, b)

        vm.reg.eflags.SF = (c >> (sz * 8 - 1)) & 1

        c &= MAXVALS[sz]

        vm.reg.eflags.ZF = c == 0
        vm.reg.eflags.PF = parity(c & 0xFF)

        if not test:
            if __debug__:
                name = operation.__name__
            type.set(loc, sz, c)
        else:
            if __debug__:
                name = 'test'

        if __debug__:
            logger.debug(
                '%s %s=%d, %s=%d',
                name,
                debug_operand(RM, sz), a,
                debug_operand(R, sz), b
            )

        return True

    def r_rm(vm, _8bit, operation, test=False) -> True:
        sz = 1 if _8bit else vm.operand_size
        RM, R = vm.process_ModRM()
        type, loc = RM

        vm.reg.eflags.OF = vm.reg.eflags.CF = 0

        a = (type).get(loc, sz)
        b = vm.reg.get(R[1], sz)

        c = operation(a, b)

        vm.reg.eflags.SF = (c >> (sz * 8 - 1)) & 1

        c &= MAXVALS[sz]

        vm.reg.eflags.ZF = c == 0
        vm.reg.eflags.PF = parity(c & 0xFF)

        if not test:
            if __debug__:
                name = operation.__name__
            vm.reg.set(R[1], sz, c)
        else:
            if __debug__:
                name = 'test'

        if __debug__:
            logger.debug(
                '%s %s=%d, %s=%d',
                name,
                debug_operand(R, sz), a,
                debug_operand(RM, sz), b
            )

        return True


####################
# NEG / NOT
####################
class NEGNOT(Instruction):
    """
    NEG: two's complement negate
    Flags:
        CF flag set to 0 if the source operand is 0; otherwise it is set to 1.
        OF (!), SF, ZF, AF(!), and PF flags are set according to the result.

    NOT: one's complement negation  (reverses bits). No flags affected.
    Flags:
        None affected
    """

    def __init__(self):
        self.opcodes = {
            # NEG, NOT
            0xF6: [
                P(self.rm, _8bit=True, REG=3),  # NEG r/m8
                P(self.rm, _8bit=True, REG=2),  # NOT r/m8
                ],
            0xF7: [
                P(self.rm, _8bit=False, REG=3),  # NEG r/m
                P(self.rm, _8bit=False, REG=2),  # NOT r/m
                ]
            }

    @staticmethod
    def operation_not(a, off):
        return MAXVALS[off] - a

    @staticmethod
    def operation_neg(a, off):
        return NEGNOT.operation_not(a, off) + 1

    def rm(vm, _8bit, REG: int) -> bool:
        ModRM = vm.mem.get_eip(vm.eip, 1)
        _REG = (ModRM & 0b00111000) >> 3

        if _REG != REG:
            return False

        operation = {2: NEGNOT.operation_not, 3: NEGNOT.operation_neg}[REG]

        sz = 1 if _8bit else vm.operand_size

        RM, R = vm.process_ModRM()
        type, loc = RM

        a = (type).get(loc, sz)
        b = operation(a, sz)

        if operation == NEGNOT.operation_neg:
            sign_b = (b >> (sz * 8 - 1)) & 1
            vm.reg.eflags.CF = a != 0
            vm.reg.eflags.SF = sign_b
            vm.reg.eflags.ZF = b == 0
            vm.reg.eflags.PF = parity(b)
            vm.reg.eflags.OF = is_signed_out_of_range(b, sz)
            # TODO: deal with AF
            # vm.reg.efags.AF = ??

        b &= MAXVALS[sz]
        (type).set(loc, sz, b)

        if __debug__:
            dbg = debug_operand(RM, sz)
            logger.debug(
                '%s %s=%d (%s := %d)',
                operation.__name__,
                dbg, a,
                dbg, b
            )

        return True


####################
# SAL / SAR / SHL / SHR
####################
class SHIFT(Instruction):
    def __init__(self):
        self.opcodes = {
            # SHL, SHR, SAR
            0xD0: [
                P(self.shift, operation=Shift.SHL, cnt=Shift.C_ONE, _8bit=True),
                P(self.shift, operation=Shift.SHR, cnt=Shift.C_ONE, _8bit=True),
                P(self.shift, operation=Shift.SAR, cnt=Shift.C_ONE, _8bit=True),
                ],
            0xD2: [
                P(self.shift, operation=Shift.SHL, cnt=Shift.C_CL, _8bit=True),
                P(self.shift, operation=Shift.SHR, cnt=Shift.C_CL, _8bit=True),
                P(self.shift, operation=Shift.SAR, cnt=Shift.C_CL, _8bit=True),
                ],
            0xC0: [
                P(self.shift, operation=Shift.SHL, cnt=Shift.C_imm8, _8bit=True),
                P(self.shift, operation=Shift.SHR, cnt=Shift.C_imm8, _8bit=True),
                P(self.shift, operation=Shift.SAR, cnt=Shift.C_imm8, _8bit=True),
                ],

            0xD1: [
                P(self.shift, operation=Shift.SHL, cnt=Shift.C_ONE, _8bit=False),
                P(self.shift, operation=Shift.SHR, cnt=Shift.C_ONE, _8bit=False),
                P(self.shift, operation=Shift.SAR, cnt=Shift.C_ONE, _8bit=False),
                ],
            0xD3: [
                P(self.shift, operation=Shift.SHL, cnt=Shift.C_CL, _8bit=False),
                P(self.shift, operation=Shift.SAR, cnt=Shift.C_CL, _8bit=False),
                P(self.shift, operation=Shift.SHR, cnt=Shift.C_CL, _8bit=False),
                ],
            0xC1: [
                P(self.shift, operation=Shift.SHL, cnt=Shift.C_imm8, _8bit=False),
                P(self.shift, operation=Shift.SHR, cnt=Shift.C_imm8, _8bit=False),
                P(self.shift, operation=Shift.SAR, cnt=Shift.C_imm8, _8bit=False)
                ]
            }

    def shift(vm, operation, cnt, _8bit) -> True:
        sz = 1 if _8bit else vm.operand_size
        old_eip = vm.eip

        sz = vm.operand_size  # WTF?!
        RM, R = vm.process_ModRM()

        if (operation == Shift.SHL) and (R[1] != 4):
            vm.eip = old_eip
            return False
        elif (operation == Shift.SHR) and (R[1] != 5):
            vm.eip = old_eip
            return False
        elif (operation == Shift.SAR) and (R[1] != 7):
            vm.eip = old_eip
            return False

        _cnt = cnt

        if cnt == Shift.C_ONE:
            cnt = 1
        elif cnt == Shift.C_CL:
            cnt = vm.reg.get(1, 1)
        elif cnt == Shift.C_imm8:
            cnt = vm.mem.get(vm.eip, 1)
            vm.eip += 1
        else:
            raise RuntimeError('Invalid count')

        countMASK = 0x1F

        tmp_cnt = cnt & countMASK

        if tmp_cnt == 0:
            return True

        type, loc = RM

        dst = (type).get(loc, sz, operation == Shift.SAR)
        tmp_dst = dst

        while tmp_cnt != 0:
            if operation == Shift.SHL:
                # vm.reg.eflags_set(Reg32.CF, (dst >> (sz * 8)) & 1)
                vm.reg.eflags.CF = MSB(dst, sz)
                dst <<= 1
            else:
                # vm.reg.eflags_set(Reg32.CF, dst & 1)
                vm.reg.eflags.CF = LSB(dst)
                dst >>= 1

            tmp_cnt -= 1

        if cnt & countMASK == 1:
            if operation == Shift.SHL:
                vm.reg.eflags.OF = MSB(dst, sz) ^ vm.reg.eflags.CF
            elif operation == Shift.SAR:
                vm.reg.eflags.OF = 0
            else:
                vm.reg.eflags.OF = MSB(tmp_dst, sz)

        sign_dst = MSB(dst, sz)
        vm.reg.eflags.SF = sign_dst

        dst &= MAXVALS[sz]

        vm.reg.eflags.ZF = dst == 0
        vm.reg.eflags.PF = parity(dst)

        (type).set(loc, sz, dst)

        if __debug__:
            name = operation.name.lower()
            op = {Shift.C_ONE: '', Shift.C_CL: 'cl', Shift.C_imm8: 'imm8'}[_cnt]

            dbg = debug_operand(RM, sz)
            logger.debug(
                '%s %s=%s, %s=%s (%s := %d)',
                name,
                dbg,
                tmp_dst, op, cnt,
                dbg, dst
            )

        return True


####################
# SHRD / SHLD
####################
class SHIFTD(Instruction):
    def __init__(self):
        self.opcodes = {
            0x0FA4: P(self.shift, operation=Shift.SHL, cnt=Shift.C_imm8),
            0x0FA5: P(self.shift, operation=Shift.SHL, cnt=Shift.C_CL),

            0x0FAC: P(self.shift, operation=Shift.SHR, cnt=Shift.C_imm8),
            0x0FAD: P(self.shift, operation=Shift.SHR, cnt=Shift.C_CL)
        }

    def shift(vm, operation, cnt) -> True:
        sz = vm.operand_size

        RM, R = vm.process_ModRM()
        type, loc = RM

        dst = (type).get(loc, sz)
        src = vm.reg.get(R[1], sz)

        dst_init = dst

        if cnt == Shift.C_imm8:
            cnt = vm.mem.get(vm.eip, 1)
            vm.eip += 1
        else:
            cnt = vm.reg.get(1, 1)

        cnt %= 32

        if cnt == 0:
            return True

        if cnt > sz * 8:
            # Bad parameters
            return True

        _sign_dst = (dst >> (sz * 8 - 1)) & 1

        _src = src >> (sz * 8 - cnt)
        if operation == Shift.SHL:
            vm.reg.eflags.CF = (dst >> (sz * 8 - cnt)) & 1
            dst <<= cnt
            dst |= _src
        else:
            vm.reg.eflags.CF = (dst >> (cnt - 1)) & 1
            dst >>= cnt
            dst |= _src << cnt

        # set flags
        sign_dst = (dst >> (sz * 8 - 1)) & 1
        vm.reg.eflags.SF = sign_dst
        dst &= MAXVALS[sz]
        vm.reg.eflags.ZF = dst == 0
        vm.reg.eflags.PF = parity(dst)

        # set OF flag
        if cnt == 1:
            vm.reg.eflags.OF = _sign_dst != sign_dst

        (type).set(loc, sz, dst)

        if __debug__:
            dbg = debug_operand(RM, sz)
            logger.debug(
                'sh%sd %s=0x%x, %s=0x%x, 0x%x (%s := 0x%x)',
                'l' if operation == Shift.SHL else 'r',
                dbg, dst_init,
                debug_operand(R, sz), src,
                cnt,
                dbg, dst,
            )

        return True
