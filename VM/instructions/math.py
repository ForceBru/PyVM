import enum

from ..debug import reg_names
from ..util import Instruction
from ..misc import parity, sign_extend

from functools import partialmethod as P

import logging
logger = logging.getLogger(__name__)

MAXVALS = [None, (1 << 8) - 1, (1 << 16) - 1, None, (1 << 32) - 1]  # MAXVALS[n] is the maximum value of an unsigned n-bit number
SIGNS   = [None, 1 << 8 - 1, 1 << 16 - 1, None, 1 << 32 - 1]  # SIGNS[n] is the maximum absolute value of a signed n-bit number


####################
# ADD / SUB / CMP / ADC / SBB
####################
class ADDSUB_operation(enum.IntFlag):
    ADD = 0
    ADC = 2
    SBB = 3
    SUB = 5
    CMP = 7


class ADDSUB(Instruction):
    """
    Perform addition or subtraction.
    Flags:
        OF, SF, ZF, AF, CF, and PF flags are set according to the result.

    Operation: c <- a [op] b

    :param sub: indicates whether the instruction to be executed is SUB. If False, ADD is executed.
    :param cmp: indicates whether the instruction to be executed is CMP.
    :param carry: indicates whether the instruction to be executed is ADC or SBB. Must be combined with the `sub` parameter.
    """

    def __init__(self):
        self.opcodes = {
            # ADD
            0x04: P(self.r_imm, _8bit=True,  sub=False, cmp=False, carry=False),
            0x05: P(self.r_imm, _8bit=False, sub=False, cmp=False, carry=False),

            0x80: [
                P(self.rm_imm, _8bit_op=1, _8bit_imm=1, REG=0),  # ADD r/m8, imm8
                P(self.rm_imm, _8bit_op=1, _8bit_imm=1, REG=5),  # SUB r/m8, imm8
                P(self.rm_imm, _8bit_op=1, _8bit_imm=1, REG=7),  # CMP r/m8, imm8
                P(self.rm_imm, _8bit_op=1, _8bit_imm=1, REG=2),  # ADC r/m8, imm8
                P(self.rm_imm, _8bit_op=1, _8bit_imm=1, REG=3),  # SBB r/m8, imm8
                ],
            0x81: [
                P(self.rm_imm, _8bit_op=0, _8bit_imm=0, REG=0),  # ADD r/m, imm
                P(self.rm_imm, _8bit_op=0, _8bit_imm=0, REG=5),  # SUB r/m, imm
                P(self.rm_imm, _8bit_op=0, _8bit_imm=0, REG=7),  # CMP r/m, imm
                P(self.rm_imm, _8bit_op=0, _8bit_imm=0, REG=2),  # ADC r/m, imm
                P(self.rm_imm, _8bit_op=0, _8bit_imm=0, REG=3),  # SBB r/m, imm
                ],
            0x83: [
                P(self.rm_imm, _8bit_op=0, _8bit_imm=1, REG=0),  # ADD r/m, imm8
                P(self.rm_imm, _8bit_op=0, _8bit_imm=1, REG=5),  # SUB r/m, imm8
                P(self.rm_imm, _8bit_op=0, _8bit_imm=1, REG=7),  # CMP r/m, imm8
                P(self.rm_imm, _8bit_op=0, _8bit_imm=1, REG=2),  # ADC r/m, imm8
                P(self.rm_imm, _8bit_op=0, _8bit_imm=1, REG=3),  # SBB r/m, imm8
                ],

            0x00: P(self.rm_r, _8bit=True,  sub=False, cmp=False, carry=False),
            0x01: P(self.rm_r, _8bit=False, sub=False, cmp=False, carry=False),
            0x02: P(self.r_rm, _8bit=True,  sub=False, cmp=False, carry=False),
            0x03: P(self.r_rm, _8bit=False, sub=False, cmp=False, carry=False),

            # SUB
            0x2C: P(self.r_imm, _8bit=True,  sub=True, cmp=False, carry=False),
            0x2D: P(self.r_imm, _8bit=False, sub=True, cmp=False, carry=False),

            0x28: P(self.rm_r, _8bit=True,  sub=True, cmp=False, carry=False),
            0x29: P(self.rm_r, _8bit=False, sub=True, cmp=False, carry=False),
            0x2A: P(self.r_rm, _8bit=True,  sub=True, cmp=False, carry=False),
            0x2B: P(self.r_rm, _8bit=False, sub=True, cmp=False, carry=False),

            # CMP
            0x3C: P(self.r_imm, _8bit=True,  sub=True, cmp=True, carry=False),
            0x3D: P(self.r_imm, _8bit=False, sub=True, cmp=True, carry=False),

            0x38: P(self.rm_r, _8bit=True,  sub=True, cmp=True, carry=False),
            0x39: P(self.rm_r, _8bit=False, sub=True, cmp=True, carry=False),
            0x3A: P(self.r_rm, _8bit=True,  sub=True, cmp=True, carry=False),
            0x3B: P(self.r_rm, _8bit=False, sub=True, cmp=True, carry=False),

            # ADC
            0x14: P(self.r_imm, _8bit=True,  sub=False, cmp=False, carry=True),
            0x15: P(self.r_imm, _8bit=False, sub=False, cmp=False, carry=True),

            0x10: P(self.rm_r, _8bit=True,  sub=False, cmp=False, carry=True),
            0x11: P(self.rm_r, _8bit=False, sub=False, cmp=False, carry=True),
            0x12: P(self.r_rm, _8bit=True,  sub=False, cmp=False, carry=True),
            0x13: P(self.r_rm, _8bit=False, sub=False, cmp=False, carry=True),

            # SBB
            0x1C: P(self.r_imm, _8bit=True,  sub=True, cmp=False, carry=True),
            0x1D: P(self.r_imm, _8bit=False, sub=True, cmp=False, carry=True),

            0x18: P(self.rm_r, _8bit=True,  sub=True, cmp=False, carry=True),
            0x19: P(self.rm_r, _8bit=False, sub=True, cmp=False, carry=True),
            0x1A: P(self.r_rm, _8bit=True,  sub=True, cmp=False, carry=True),
            0x1B: P(self.r_rm, _8bit=False, sub=True, cmp=False, carry=True),
            }

    def r_imm(vm, _8bit, sub: bool, cmp: bool, carry: bool) -> True:
        sz = 1 if _8bit else vm.operand_size

        b = vm.mem.get(vm.eip, sz)
        vm.eip += sz

        if carry:
            b += vm.reg.eflags.CF

        a = vm.reg.get(0, sz)

        c = a + (b if not sub else MAXVALS[sz] + 1 - b)

        sign_a = (a >> (sz * 8 - 1)) & 1
        sign_b = (b >> (sz * 8 - 1)) & 1
        sign_c = (c >> (sz * 8 - 1)) & 1

        if not sub:
            vm.reg.eflags.OF = (sign_a == sign_b) and (sign_a != sign_c)
            vm.reg.eflags.CF = c > MAXVALS[sz]
            vm.reg.eflags.AF = ((a & 255) + (b & 255)) > MAXVALS[1]
        else:
            vm.reg.eflags.OF = (sign_a != sign_b) and (sign_a != sign_c)
            vm.reg.eflags.CF = b > a
            vm.reg.eflags.AF = (b & 255) > (a & 255)

        c &= MAXVALS[sz]

        vm.reg.eflags.SF = sign_c
        vm.reg.eflags.ZF = c == 0
        vm.reg.eflags.PF = parity(c)

        if not cmp:
            vm.reg.set(0, sz, c)

        logger.debug(
            '%s %s=%d, imm%d=%d (%s := %d)',
            ('sbb' if sub else 'adc') if carry else ('cmp' if cmp else ('sub' if sub else 'add')),
            reg_names[0][sz], a,
            sz * 8, b,
            reg_names[0][sz], c
        )

        return True

    def rm_imm(vm, _8bit_op: bool, _8bit_imm: bool, REG: int) -> bool:
        ModRM = vm.mem.get_eip(vm.eip, 1)
        _REG = (ModRM & 0b00111000) >> 3

        if _REG != REG:
            return False

        operation = ADDSUB_operation(REG)

        sz = 1 if _8bit_op else vm.operand_size
        imm_sz = 1 if _8bit_imm else vm.operand_size

        RM, R = vm.process_ModRM(sz)

        b = vm.mem.get(vm.eip, imm_sz, True)
        vm.eip += imm_sz

        b &= MAXVALS[sz]  # convert to an unsigned number; ATTENTION!

        if operation == operation.ADC or operation == operation.SBB:
            b += vm.reg.eflags.CF

        type, loc, _ = RM

        a = (type).get(loc, sz)

        c = a + (b if operation == operation.ADD or operation == operation.ADC else MAXVALS[sz] + 1 - b)

        sign_a = (a >> (sz * 8 - 1)) & 1
        sign_b = (b >> (sz * 8 - 1)) & 1
        sign_c = (c >> (sz * 8 - 1)) & 1

        if operation == operation.ADD or operation == operation.ADC:  # not in (operation.SBB, operation.SUB, operation.CMP):
            vm.reg.eflags.OF = (sign_a == sign_b) and (sign_a != sign_c)
            vm.reg.eflags.CF = c > MAXVALS[sz]
            vm.reg.eflags.AF = ((a & 255) + (b & 255)) > MAXVALS[1]
        else:
            vm.reg.eflags.OF = (sign_a != sign_b) and (sign_a != sign_c)
            vm.reg.eflags.CF = b > a
            vm.reg.eflags.AF = (b & 255) > (a & 255)

        c &= MAXVALS[sz]

        vm.reg.eflags.SF = sign_c
        vm.reg.eflags.ZF = c == 0
        vm.reg.eflags.PF = parity(c)

        if operation != operation.CMP:
            (type).set(loc, sz, c)

        logger.debug('%s %s=%d, imm%d=%d (%s := %d)',
                     operation.name,
                     hex(loc) if type else reg_names[loc][sz],
                     a, sz * 8, b,
                     hex(loc) if type else reg_names[loc][sz], c
                     )
        
        return True

    def rm_r(vm, _8bit, sub: bool, cmp: bool, carry: bool) -> True:
        sz = 1 if _8bit else vm.operand_size

        RM, R = vm.process_ModRM(sz, sz)

        type, loc, _ = RM

        a = (type).get(loc, sz)
        b = vm.reg.get(R[1], sz)

        if carry:
            b += vm.reg.eflags.CF

        c = a + (b if not sub else MAXVALS[sz] + 1 - b)

        sign_a = (a >> (sz * 8 - 1)) & 1
        sign_b = (b >> (sz * 8 - 1)) & 1
        sign_c = (c >> (sz * 8 - 1)) & 1

        if not sub:
            vm.reg.eflags.OF = (sign_a == sign_b) and (sign_a != sign_c)
            vm.reg.eflags.CF = c > MAXVALS[sz]
            vm.reg.eflags.AF = ((a & 255) + (b & 255)) > MAXVALS[1]
        else:
            vm.reg.eflags.OF = (sign_a != sign_b) and (sign_a != sign_c)
            vm.reg.eflags.CF = b > a
            vm.reg.eflags.AF = (b & 255) > (a & 255)

        c &= MAXVALS[sz]

        vm.reg.eflags.SF = sign_c
        vm.reg.eflags.ZF = c == 0
        vm.reg.eflags.PF = parity(c)

        if not cmp:
            (type).set(loc, sz, c)

        logger.debug('%s %s=%d, %s=%d (%s := %d)',
                     ('sbb' if sub else 'adc') if carry else ('cmp' if cmp else ('sub' if sub else 'add')),
                     hex(loc) if type else reg_names[loc][sz], a,
                     reg_names[R[1]][R[2]], b,
                     hex(loc) if type else reg_names[loc][sz], c
                     )

        return True

    def r_rm(vm, _8bit, sub=False, cmp=False, carry=False) -> True:
        sz = 1 if _8bit else vm.operand_size

        RM, R = vm.process_ModRM(sz, sz)

        type, loc, _ = RM

        b = (type).get(loc, sz)
        a = vm.reg.get(R[1], sz)

        if carry:
            b += vm.reg.eflags.CF

        c = a + (b if not sub else MAXVALS[sz] + 1 - b)

        sign_a = (a >> (sz * 8 - 1)) & 1
        sign_b = (b >> (sz * 8 - 1)) & 1
        sign_c = (c >> (sz * 8 - 1)) & 1

        if not sub:
            vm.reg.eflags.OF = (sign_a == sign_b) and (sign_a != sign_c)
            vm.reg.eflags.CF = c > MAXVALS[sz]
            vm.reg.eflags.AF = ((a & 255) + (b & 255)) > MAXVALS[1]
        else:
            vm.reg.eflags.OF = (sign_a != sign_b) and (sign_a != sign_c)
            vm.reg.eflags.CF = b > a
            vm.reg.eflags.AF = (b & 255) > (a & 255)

        c &= MAXVALS[sz]

        vm.reg.eflags.SF = sign_c
        vm.reg.eflags.ZF = c == 0
        vm.reg.eflags.PF = parity(c)

        if not cmp:
            vm.reg.set(R[1], sz, c)

        logger.debug('%s %s=%d, %s=%d (%s := %d)',
                     ('sbb' if sub else 'adc') if carry else ('cmp' if cmp else ('sub' if sub else 'add')),
                     reg_names[R[1]][R[2]], a,
                     hex(loc) if type else reg_names[loc][sz], b,
                     reg_names[R[1]][R[2]], c
                     )

        return True


####################
# INC / DEC
####################
class INCDEC(Instruction):
    """
    Increment or decrement r/m8/16/32 by 1

    Flags:
        CF not affected
        OF, SF, ZF, AF, PF set according to the result

    Operation: c <- a +/- 1

    :param dec: whether the instruction to be executed is DEC. If False, INC is executed.
    """

    def __init__(self):
        self.opcodes = {
            # INC
            **{
                o: P(self.r, _8bit=False, dec=False)
                for o in range(0x40, 0x48)
                },
            0xFE: [
                P(self.rm, _8bit=True, REG=0),  # INC r/m8
                P(self.rm, _8bit=True, REG=1)   # DEC r/m8
                ],
            0xFF: [
                P(self.rm, _8bit=False, REG=0),  # INC r/m
                P(self.rm, _8bit=False, REG=1)   # DEC r/m
                ],

            # DEC
            **{
                o: P(self.r, _8bit=False, dec=True)
                for o in range(0x48, 0x50)
                }
            }

    def rm(vm, _8bit: bool, REG: int) -> bool:
        ModRM = vm.mem.get_eip(vm.eip, 1)
        _REG = (ModRM & 0b00111000) >> 3

        if _REG != REG:
            return False

        dec = REG
        sz = 1 if _8bit else vm.operand_size

        RM, R = vm.process_ModRM(sz)

        type, loc, _ = RM

        a = (type).get(loc, sz)
        b = 1

        c = a + (b if not dec else MAXVALS[sz] - 1 + b)

        sign_a = (a >> (sz * 8 - 1)) & 1
        sign_b = (b >> (sz * 8 - 1)) & 1
        sign_c = (c >> (sz * 8 - 1)) & 1

        if not dec:
            vm.reg.eflags.OF = (sign_a == sign_b) and (sign_a != sign_c)
            vm.reg.eflags.AF = ((a & 255) + (b & 255)) > MAXVALS[1]
        else:
            vm.reg.eflags.OF = (sign_a != sign_b) and (sign_a != sign_c)
            vm.reg.eflags.AF = (b & 255) > (a & 255)

        c &= MAXVALS[sz]

        vm.reg.eflags.SF = sign_c
        vm.reg.eflags.ZF = c == 0
        vm.reg.eflags.PF = parity(c)

        (type).set(loc, sz, c)

        logger.debug('%s %s=%d', 'dec' if dec else 'inc', hex(loc) if type else reg_names[loc][sz], a)

        return True

    def r(vm, _8bit, dec=False) -> True:
        sz = 1 if _8bit else vm.operand_size
        loc = vm.opcode & 0b111

        a = vm.reg.get(loc, sz)
        b = 1

        c = a + (b if not dec else MAXVALS[sz] - 1 + b)

        sign_a = (a >> (sz * 8 - 1)) & 1
        sign_b = (b >> (sz * 8 - 1)) & 1
        sign_c = (c >> (sz * 8 - 1)) & 1

        if not dec:
            vm.reg.eflags.OF = (sign_a == sign_b) and (sign_a != sign_c)
            vm.reg.eflags.AF = ((a & 255) + (b & 255)) > MAXVALS[1]
        else:
            vm.reg.eflags.OF = (sign_a != sign_b) and (sign_a != sign_c)
            vm.reg.eflags.AF = (b & 255) > (a & 255)

        c &= MAXVALS[sz]

        vm.reg.eflags.SF = sign_c
        vm.reg.eflags.ZF = c == 0
        vm.reg.eflags.PF = parity(c)

        vm.reg.set(loc, sz, c)

        logger.debug('%s %s := %d', 'dec' if dec else 'inc', reg_names[loc][sz], c)

        return True

####################
# MUL
####################
class MUL(Instruction):
    def __init__(self):
        self.opcodes = {
            0xF6: P(self.mul, _8bit=True),
            0xF7: P(self.mul, _8bit=False)
            }

    def mul(vm, _8bit) -> bool:
        """
        Unsigned multiply.
        AX      <-  AL * r/m8
        DX:AX   <-  AX * r/m16
        EDX:EAX <- EAX * r/m32
        """
        sz = 1 if _8bit else vm.operand_size

        old_eip = vm.eip

        RM, R = vm.process_ModRM(sz, sz)

        if R[1] != 4:
            vm.eip = old_eip
            return False  # This is not MUL

        type, loc, _ = RM

        a = (type).get(loc, sz)
        b = vm.reg.get(0, sz)  # AL/AX/EAX

        res = a * b

        _sz = 2 if sz == 1 else sz
        lo = res & MAXVALS[_sz]
        hi = (res >> (sz * 8)) & MAXVALS[_sz]

        upper_half_not_zero = hi != 0
        vm.reg.eflags.OF = vm.reg.eflags.CF = upper_half_not_zero

        vm.reg.set(0, _sz, lo)  # (E)AX

        if sz != 1:
            vm.reg.set(2, _sz, hi)  # (E)DX

        logger.debug(
            'mul %s=%d, %s=%d (edx := 0x%x; eax := 0x%x)',
            reg_names[0][sz],
            b, hex(loc) if type else reg_names[loc][sz], a,
            hi, lo
        )

        return True

####################
# DIV / IDIV
####################
class DIV(Instruction):
    def __init__(self):
        self.opcodes = {
            0xF6: [
                P(self.div, _8bit=True, REG=6),  # DIV r/m8
                P(self.div, _8bit=True, REG=7)  # IDIV r/m8
                ],
            0xF7: [
                P(self.div, _8bit=False, REG=6),  # DIV r/m
                P(self.div, _8bit=False, REG=7)   # IDIV r/m
                ]
            }

    def div(vm, _8bit, REG: int) -> bool:
        """
        Unsigned divide.
        AL, AH = divmod(AX, r/m8)
        AX, DX = divmod(DX:AX, r/m16)
        EAX, EDX = divmod(EDX:EAX, r/m32)
        """
        ModRM = vm.mem.get_eip(vm.eip, 1)
        _REG = (ModRM & 0b00111000) >> 3

        if _REG != REG:
            return False

        idiv = REG == 7

        sz = 1 if _8bit else vm.operand_size

        RM, R = vm.process_ModRM(sz)
        type, loc, _ = RM

        divisor = (type).get(loc, sz, idiv)

        if divisor == 0:
            raise ZeroDivisionError

        if sz == 1:
            dividend = vm.reg.get(0, sz * 2)  # AX
        else:
            high = vm.reg.get(2, sz)  # DX/EDX
            low = vm.reg.get(0, sz)  # AX/EAX
            dividend = (high << (sz * 8)) + low
        
        if idiv:
            dividend = sign_extend(dividend, sz * 2)

        quot, rem = dividend // divisor, dividend % divisor

        if quot > MAXVALS[sz]:
            raise RuntimeError('Divide error')

        vm.reg.set(0, sz, quot)  # AL/AX/EAX
        if sz == 1:
            vm.reg.set(4, sz, rem)  # AH
        else:
            vm.reg.set(2, sz, rem)  # DX/EDX

        logger.debug(
            '%sdiv %s=%d, %s=%d',
            'i' if idiv else '',
            reg_names[0][sz], dividend,
            hex(loc) if type else reg_names[loc][sz], divisor
        )

        return True

####################
# IMUL
####################
class IMUL(Instruction):
    def __init__(self):
        self.opcodes = {
            0xF6  : P(self.rm, _8bit=True),
            0xF7  : P(self.rm, _8bit=False),

            0x0FAF: self.r_rm,

            0x6B  : P(self.r_rm_imm, _8bit_imm=True),
            0x69  : P(self.r_rm_imm, _8bit_imm=False)
            }

    def rm(vm, _8bit: int) -> bool:
        sz = 1 if _8bit else vm.operand_size

        old_eip = vm.eip

        RM, R = vm.process_ModRM(sz, sz)

        if R[1] != 5:
            vm.eip = old_eip
            return False  # This is not IMUL

        type, loc, _ = RM

        src = (type).get(loc, sz, True)
        dst = vm.reg.get(0, sz, True)  # AL/AX/EAX

        tmp_xp = src * dst

        _sz = 2 if sz == 1 else sz
        lo = tmp_xp & MAXVALS[_sz]
        hi = (tmp_xp >> (sz * 8)) & MAXVALS[_sz]

        vm.reg.set(0, _sz, lo)  # (E)AX

        if sz != 1:
            vm.reg.set(2, _sz, hi)  # (E)DX

        set_flags = sign_extend(tmp_xp >> (sz * 8), sz) != tmp_xp

        vm.reg.eflags.OF = vm.reg.eflags.CF = set_flags

        logger.debug(
            'imul %s=%d, %s=%d (%s := %d; %s := %d)',
            reg_names[0][sz], dst,
            hex(loc) if type else reg_names[loc][sz], src,
            reg_names[2][_sz], hi,
            reg_names[0][_sz], lo
        )

        return True

    def r_rm(vm) -> True:
        sz = vm.operand_size

        RM, R = vm.process_ModRM(sz, sz)

        type, loc, _ = RM

        src = (type).get(loc, sz, True)
        dst = vm.reg.get(R[1], sz, True)

        tmp_xp = src * dst
        dest = tmp_xp & MAXVALS[sz]

        vm.reg.set(R[1], sz, dest)

        set_flags = sign_extend(dest >> (sz * 8), sz) != tmp_xp

        vm.reg.eflags.OF = vm.reg.eflags.CF = set_flags

        logger.debug('imul %s=%d, %s=%d', reg_names[R[1]][sz], dst, hex(loc) if type else reg_names[loc][sz], src)

        return True

    def r_rm_imm(vm, _8bit_imm: int) -> True:
        sz = vm.operand_size
        imm_sz = 1 if _8bit_imm else vm.operand_size

        RM, R = vm.process_ModRM(sz)

        src1 = vm.mem.get_eip(vm.eip, imm_sz, True)
        vm.eip += imm_sz

        type, loc, _ = RM

        src2 = (type).get(loc, sz, True)

        tmp_xp = src1 * src2

        # set_flags = sign_extend(tmp_xp[:sz], sz) != tmp_xp
        DEST = tmp_xp & MAXVALS[sz]
        set_flags = sign_extend(DEST, sz) != tmp_xp

        vm.reg.eflags.OF = vm.reg.eflags.CF = set_flags

        #vm.reg.set(R[1], sz, tmp_xp[:sz])
        vm.reg.set(R[1], sz, DEST)

        logger.debug('imul %s := %d, %s=%d, imm%d=%d',
                     reg_names[R[1]][sz],
                     DEST,
                     hex(loc) if type else reg_names[loc][sz],
                     src2, sz * 8, src1)

        return True
