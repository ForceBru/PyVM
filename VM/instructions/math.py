from ..debug import *
from ..Registers import Reg32
from ..util import Instruction, to_int, byteorder
from ..misc import parity, sign_extend

from functools import partialmethod as P

import logging
logger = logging.getLogger(__name__)

MAXVALS = [None, (1 << 8) - 1, (1 << 16) - 1, None, (1 << 32) - 1]  # MAXVALS[n] is the maximum value of an unsigned n-bit number
SIGNS   = [None, 1 << 8 - 1, 1 << 16 - 1, None, 1 << 32 - 1]  # SIGNS[n] is the maximum absolute value of a signed n-bit number

####################
# ADD / SUB / CMP / ADC / SBB
####################
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
            0x04: P(self.r_imm, _8bit=True),
            0x05: P(self.r_imm, _8bit=False),

            0x80: [
                P(self.rm_imm, _8bit_op=True, _8bit_imm=True),
                P(self.rm_imm, _8bit_op=True, _8bit_imm=True, sub=True),
                P(self.rm_imm, _8bit_op=True, _8bit_imm=True, sub=True, cmp=True),
                P(self.rm_imm, _8bit_op=True, _8bit_imm=True, carry=True),
                P(self.rm_imm, _8bit_op=True, _8bit_imm=True, sub=True, carry=True),
                ],
            0x81: [
                P(self.rm_imm, _8bit_op=False, _8bit_imm=False),
                P(self.rm_imm, _8bit_op=False, _8bit_imm=False, sub=True),
                P(self.rm_imm, _8bit_op=False, _8bit_imm=False, sub=True, cmp=True),
                P(self.rm_imm, _8bit_op=False, _8bit_imm=False, carry=True),
                P(self.rm_imm, _8bit_op=False, _8bit_imm=False, sub=True, carry=True),
                ],
            0x83: [
                P(self.rm_imm, _8bit_op=False, _8bit_imm=True),
                P(self.rm_imm, _8bit_op=False, _8bit_imm=True, sub=True),
                P(self.rm_imm, _8bit_op=False, _8bit_imm=True, sub=True, cmp=True),
                P(self.rm_imm, _8bit_op=False, _8bit_imm=True, carry=True),
                P(self.rm_imm, _8bit_op=False, _8bit_imm=True, sub=True, carry=True),
                ],

            0x00: P(self.rm_r, _8bit=True),
            0x01: P(self.rm_r, _8bit=False),
            0x02: P(self.r_rm, _8bit=True),
            0x03: P(self.r_rm, _8bit=False),

            # SUB
            0x2C: P(self.r_imm, _8bit=True, sub=True),
            0x2D: P(self.r_imm, _8bit=False, sub=True),

            0x28: P(self.rm_r, _8bit=True, sub=True),
            0x29: P(self.rm_r, _8bit=False, sub=True),
            0x2A: P(self.r_rm, _8bit=True, sub=True),
            0x2B: P(self.r_rm, _8bit=False, sub=True),

            # CMP
            0x3C: P(self.r_imm, _8bit=True, sub=True, cmp=True),
            0x3D: P(self.r_imm, _8bit=False, sub=True, cmp=True),

            0x38: P(self.rm_r, _8bit=True, sub=True, cmp=True),
            0x39: P(self.rm_r, _8bit=False, sub=True, cmp=True),
            0x3A: P(self.r_rm, _8bit=True, sub=True, cmp=True),
            0x3B: P(self.r_rm, _8bit=False, sub=True, cmp=True),

            # ADC
            0x14: P(self.r_imm, _8bit=True, carry=True),
            0x15: P(self.r_imm, _8bit=False, carry=True),

            0x10: P(self.rm_r, _8bit=True, carry=True),
            0x11: P(self.rm_r, _8bit=False, carry=True),
            0x12: P(self.r_rm, _8bit=True, carry=True),
            0x13: P(self.r_rm, _8bit=False, carry=True),

            # SBB
            0x1C: P(self.r_imm, _8bit=True, sub=True, carry=True),
            0x1D: P(self.r_imm, _8bit=False, sub=True, carry=True),

            0x18: P(self.rm_r, _8bit=True, sub=True, carry=True),
            0x19: P(self.rm_r, _8bit=False, sub=True, carry=True),
            0x1A: P(self.r_rm, _8bit=True, sub=True, carry=True),
            0x1B: P(self.r_rm, _8bit=False, sub=True, carry=True),
            }

    def r_imm(vm, _8bit, sub=False, cmp=False, carry=False) -> True:
        sz = 1 if _8bit else vm.operand_size

        b = vm.mem.get(vm.eip, sz)
        vm.eip += sz
        b = to_int(b)

        if carry:
            b += vm.reg.eflags_get(Reg32.CF)

        a = to_int(vm.reg.get(0, sz))

        c = a + (b if not sub else MAXVALS[sz] + 1 - b)

        sign_a = (a >> (sz * 8 - 1)) & 1
        sign_b = (b >> (sz * 8 - 1)) & 1
        sign_c = (c >> (sz * 8 - 1)) & 1

        if not sub:
            vm.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.CF, c > MAXVALS[sz])
            vm.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
        else:
            vm.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.CF, b > a)
            vm.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))

        vm.reg.eflags_set(Reg32.SF, sign_c)

        c &= MAXVALS[sz]

        vm.reg.eflags_set(Reg32.ZF, c == 0)

        c = c.to_bytes(sz, byteorder)

        vm.reg.eflags_set(Reg32.PF, parity(c[0], sz))

        if not cmp:
            vm.reg.set(0, c)

        name = 'cmp' if cmp else ('sub' if sub else 'add')

        logger.debug('%s %s, imm%d=%d', name, reg_names[0][sz], sz * 8, b)
        # if debug: print('{} {}, imm{}({})'.format('cmp' if cmp else name, reg_names[0][sz], sz * 8, b))

        return True

    def rm_imm(vm, _8bit_op, _8bit_imm, sub=False, cmp=False, carry=False) -> bool:
        sz = 1 if _8bit_op else vm.operand_size
        imm_sz = 1 if _8bit_imm else vm.operand_size

        assert sz >= imm_sz
        old_eip = vm.eip

        RM, R = vm.process_ModRM(sz, sz)

        if not sub:
            if (not carry) and (R[1] != 0):
                vm.eip = old_eip
                return False  # this is not ADD
            elif carry and (R[1] != 2):
                vm.eip = old_eip
                return False  # this is not ADC
        elif sub:
            if not carry:
                if not cmp and (R[1] != 5):
                    vm.eip = old_eip
                    return False  # this is not SUB
                elif cmp and (R[1] != 7):
                    vm.eip = old_eip
                    return False  # this is not CMP
            else:
                if R[1] != 3:
                    vm.eip = old_eip
                    return False  # this is not SBB

        b = vm.mem.get(vm.eip, imm_sz)
        vm.eip += imm_sz
        b = sign_extend(b, sz)
        b = to_int(b)

        if carry:
            b += vm.reg.eflags_get(Reg32.CF)

        type, loc, _ = RM

        a = to_int((vm.mem if type else vm.reg).get(loc, sz))
        c = a + (b if not sub else MAXVALS[sz] + 1 - b)

        sign_a = (a >> (sz * 8 - 1)) & 1
        sign_b = (b >> (sz * 8 - 1)) & 1
        sign_c = (c >> (sz * 8 - 1)) & 1

        if not sub:
            vm.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.CF, c > MAXVALS[sz])
            vm.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
        else:
            vm.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.CF, b > a)
            vm.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))

        vm.reg.eflags_set(Reg32.SF, sign_c)

        c &= MAXVALS[sz]

        vm.reg.eflags_set(Reg32.ZF, c == 0)

        c = c.to_bytes(sz, byteorder)

        vm.reg.eflags_set(Reg32.PF, parity(c[0], sz))

        if not cmp:
            (vm.mem if type else vm.reg).set(loc, c)

        logger.debug('%s %s=%d, imm%d=%d',
                     'cmp' if cmp else ('sub' if sub else 'add'),
                     hex(loc) if type else reg_names[loc][sz],
                     a, sz * 8, b)
        # if debug:
        # name = 'cmp' if cmp else ('sub' if sub else 'add')
        # print(f'{name} {hex(loc) if type else reg_names[loc][sz]}, {b}')

        return True

    def rm_r(vm, _8bit, sub=False, cmp=False, carry=False) -> True:
        sz = 1 if _8bit else vm.operand_size

        RM, R = vm.process_ModRM(sz, sz)

        type, loc, _ = RM

        a = to_int((vm.mem if type else vm.reg).get(loc, sz))
        b = to_int(vm.reg.get(R[1], sz))

        if carry:
            b += vm.reg.eflags_get(Reg32.CF)

        c = a + (b if not sub else MAXVALS[sz] + 1 - b)

        sign_a = (a >> (sz * 8 - 1)) & 1
        sign_b = (b >> (sz * 8 - 1)) & 1
        sign_c = (c >> (sz * 8 - 1)) & 1

        if not sub:
            vm.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.CF, c > MAXVALS[sz])
            vm.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
        else:
            vm.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.CF, b > a)
            vm.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))

        vm.reg.eflags_set(Reg32.SF, sign_c)

        c &= MAXVALS[sz]

        vm.reg.eflags_set(Reg32.ZF, c == 0)

        c = c.to_bytes(sz, byteorder)

        vm.reg.eflags_set(Reg32.PF, parity(c[0], sz))

        if not cmp:
            (vm.mem if type else vm.reg).set(loc, c)

        logger.debug('%s %s=%d, %s=%d',
                     'cmp' if cmp else ('sub' if sub else 'add'),
                     hex(loc) if type else reg_names[loc][sz], a,
                     reg_names[R[1]][R[2]], b
                     )
        # if debug:
        # name = 'cmp' if cmp else ('sub' if sub else 'add')
        # print(f'{name} {hex(loc) if type else reg_names[loc][sz]}, {reg_names[R[1]][R[2]]}')

        return True

    def r_rm(vm, _8bit, sub=False, cmp=False, carry=False) -> True:
        sz = 1 if _8bit else vm.operand_size

        RM, R = vm.process_ModRM(sz, sz)

        type, loc, _ = RM

        b = to_int((vm.mem if type else vm.reg).get(loc, sz))
        a = to_int(vm.reg.get(R[1], sz))

        if carry:
            b += vm.reg.eflags_get(Reg32.CF)

        c = a + (b if not sub else MAXVALS[sz] + 1 - b)

        sign_a = (a >> (sz * 8 - 1)) & 1
        sign_b = (b >> (sz * 8 - 1)) & 1
        sign_c = (c >> (sz * 8 - 1)) & 1

        if not sub:
            vm.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.CF, c > MAXVALS[sz])
            vm.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
        else:
            vm.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.CF, b > a)
            vm.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))

        vm.reg.eflags_set(Reg32.SF, sign_c)

        c &= MAXVALS[sz]

        vm.reg.eflags_set(Reg32.ZF, c == 0)

        c = c.to_bytes(sz, byteorder)

        vm.reg.eflags_set(Reg32.PF, parity(c[0], sz))

        if not cmp:
            vm.reg.set(R[1], c)

        logger.debug('%s %s=%d, %s=%d',
                     'cmp' if cmp else ('sub' if sub else 'add'),
                     reg_names[R[1]][R[2]], a,
                     hex(loc) if type else reg_names[loc][sz], b
                     )
        # name = 'sub' if sub else 'add'
        # if debug: print(
        # '{0} r{1}({2}),{4}{1}({3})'.format('cmp' if cmp else name, sz * 8, R[1], hex(loc), ('m' if type else '_r')))

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
                o: P(self.r, _8bit=False)
                for o in range(0x40, 0x48)
                },
            0xFE: [
                P(self.rm, _8bit=True),
                P(self.rm, _8bit=True, dec=True)
                ],
            0xFF: [
                P(self.rm, _8bit=False),
                P(self.rm, _8bit=False, dec=True)
                ],

            # DEC
            **{
                o: P(self.r, _8bit=False, dec=True)
                for o in range(0x48, 0x50)
                }
            }

    def rm(vm, _8bit, dec=False) -> bool:
        sz = 1 if _8bit else vm.operand_size
        old_eip = vm.eip

        RM, R = vm.process_ModRM(sz, sz)

        if (not dec) and (R[1] != 0):
            vm.eip = old_eip
            return False  # this is not INC
        elif dec and (R[1] != 1):
            vm.eip = old_eip
            return False  # this is not DEC

        type, loc, _ = RM

        a = to_int((vm.mem if type else vm.reg).get(loc, sz))
        b = 1

        c = a + (b if not dec else MAXVALS[sz] - 1 + b)

        sign_a = (a >> (sz * 8 - 1)) & 1
        sign_b = (b >> (sz * 8 - 1)) & 1
        sign_c = (c >> (sz * 8 - 1)) & 1

        if not dec:
            vm.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
        else:
            vm.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))

        vm.reg.eflags_set(Reg32.SF, sign_c)

        c &= MAXVALS[sz]

        vm.reg.eflags_set(Reg32.ZF, c == 0)

        c = c.to_bytes(sz, byteorder)

        vm.reg.eflags_set(Reg32.PF, parity(c[0], sz))

        (vm.mem if type else vm.reg).set(loc, c)

        logger.debug('%s %s=%d', 'dec' if dec else 'inc', hex(loc) if type else reg_names[loc][sz], a)
        # if debug: print('{3} {0}{1}({2})'.format('m' if type else '_r', sz * 8, loc, 'dec' if dec else 'inc'))

        return True

    def r(vm, _8bit, dec=False) -> True:
        sz = 1 if _8bit else vm.operand_size
        loc = vm.opcode & 0b111

        a = to_int(vm.reg.get(loc, sz))
        b = 1

        c = a + (b if not dec else MAXVALS[sz] - 1 + b)

        sign_a = (a >> (sz * 8 - 1)) & 1
        sign_b = (b >> (sz * 8 - 1)) & 1
        sign_c = (c >> (sz * 8 - 1)) & 1

        if not dec:
            vm.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
        else:
            vm.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))

        vm.reg.eflags_set(Reg32.SF, sign_c)

        c &= MAXVALS[sz]

        vm.reg.eflags_set(Reg32.ZF, c == 0)

        c = c.to_bytes(sz, byteorder)

        vm.reg.eflags_set(Reg32.PF, parity(c[0], sz))

        vm.reg.set(loc, c)

        logger.debug('%s %=%d', 'dec' if 'dec' else 'inc', reg_names[loc][sz], a)
        # if debug: print('{3} {0}{1}({2})'.format('r', sz * 8, loc, 'dec' if dec else 'inc'))

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

    def mul(self, _8bit) -> bool:
        """
        Unsigned multiply.
        AX      <-  AL * r/m8
        DX:AX   <-  AX * r/m16
        EDX:EAX <- EAX * r/m32
        """
        sz = 1 if _8bit else self.operand_size

        old_eip = self.eip

        RM, R = self.process_ModRM(sz, sz)

        if R[1] != 4:
            self.eip = old_eip
            return False  # This is not MUL

        type, loc, _ = RM

        a = to_int((self.mem if type else self.reg).get(loc, sz))
        b = to_int(self.reg.get(0, sz))  # AL/AX/EAX

        res = (a * b).to_bytes(sz * 2, byteorder)

        upper_half_not_zero = sum(res[len(res)//2:]) != 0
        self.reg.eflags_set(Reg32.OF, upper_half_not_zero)
        self.reg.eflags_set(Reg32.CF, upper_half_not_zero)

        if sz == 1:
            self.reg.set(0, res)  # AX
        else:
            self.reg.set(2, res[:sz])  # DX/EDX
            self.reg.set(0, res[sz:])  # AX/EAX

        logger.debug('mul %s=%d, %s=%d', reg_names[0][sz], b, hex(loc) if type else reg_names[loc][sz], a,)
        # if debug: print('mul {}{}'.format('m' if type else '_r', sz * 8))
        return True

####################
# DIV / IDIV
####################
class DIV(Instruction):
    def __init__(self):
        self.opcodes = {
            0xF6: [
                P(self.div, _8bit=True),
                P(self.div, _8bit=True, idiv=True)
                ],
            0xF7: [
                P(self.div, _8bit=False),
                P(self.div, _8bit=False, idiv=True)
                ]
            }

    def div(self, _8bit, idiv=False) -> bool:
        """
        Unsigned divide.
        AL, AH = divmod(AX, r/m8)
        AX, DX = divmod(DX:AX, r/m16)
        EAX, EDX = divmod(EDX:EAX, r/m32)
        """
        sz = 1 if _8bit else self.operand_size

        old_eip = self.eip

        RM, R = self.process_ModRM(sz, sz)

        if (not idiv) and (R[1] != 6):
            self.eip = old_eip
            return False  # This is not DIV
        elif idiv and (R[1] != 7):
            self.eip = old_eip
            return False  # This is not IDIV

        type, loc, _ = RM

        divisor = to_int((self.mem if type else self.reg).get(loc, sz), idiv)

        if divisor == 0:
            raise ZeroDivisionError

        if sz == 1:
            dividend = to_int(self.reg.get(0, sz * 2), idiv)  # AX
        else:
            high = self.reg.get(2, sz)  # DX/EDX
            low = self.reg.get(0, sz)  # AX/EAX
            dividend = to_int(low + high, signed=idiv)

        quot, rem = divmod(dividend, divisor)

        if quot > MAXVALS[sz]:
            raise RuntimeError('Divide error')

        quot = quot.to_bytes(sz, byteorder, signed=idiv)
        rem = rem.to_bytes(sz, byteorder, signed=idiv)

        self.reg.set(0, quot)  # AL/AX/EAX
        if sz == 1:
            self.reg.set(4, rem)  # AH
        else:
            self.reg.set(2, rem)  # DX/EDX

        logger.debug('%sdiv %s=%d, %s=%d', 'i' if idiv else '', reg_names[0][sz], dividend, hex(loc) if type else reg_names[loc][sz], divisor)
        # if debug: print('{}div {}{}'.format('i' if idiv else '', 'm' if type else '_r', sz * 8))

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

        src = to_int((vm.mem if type else vm.reg).get(loc, sz), True)
        dst = to_int(vm.reg.get(0, sz), True)  # AL/AX/EAX

        tmp_xp = (src * dst).to_bytes(sz * 2, byteorder, signed=True)

        set_flags = sign_extend(tmp_xp[:sz], sz * 2) != tmp_xp

        vm.reg.eflags_set(Reg32.OF, set_flags)
        vm.reg.eflags_set(Reg32.CF, set_flags)

        if sz == 1:
            vm.reg.set(0, tmp_xp)  # AX
        else:
            vm.reg.set(2, tmp_xp[:sz])  # DX/EDX
            vm.reg.set(0, tmp_xp[sz:])  # AX/EAX

        logger.debug('imul %s=%d, %s=%d', reg_names[0][sz], dst, hex(loc) if type else reg_names[loc][sz], src)
        # if debug: print('imul {}{}'.format('m' if type else '_r', sz * 8))
        return True

    def r_rm(vm) -> True:
        sz = vm.operand_size

        RM, R = vm.process_ModRM(sz, sz)

        type, loc, _ = RM

        src = to_int((vm.mem if type else vm.reg).get(loc, sz), True)
        dst = to_int(vm.reg.get(R[1], sz), True)

        tmp_xp = (src * dst).to_bytes(sz * 2, byteorder, signed=True)

        set_flags = sign_extend(tmp_xp[:sz], sz * 2) != tmp_xp

        vm.reg.eflags_set(Reg32.OF, set_flags)
        vm.reg.eflags_set(Reg32.CF, set_flags)

        vm.reg.set(R[1], tmp_xp[:sz])

        logger.debug('imul %s=%d, %s=%d', reg_names[R[1]][sz], dst, hex(loc) if type else reg_names[loc][sz], src)
        # if debug: print('imul r{1}, {0}{1}'.format('m' if type else '_r', sz * 8))
        return True

    def r_rm_imm(vm, _8bit_imm: int) -> True:
        sz = vm.operand_size
        imm_sz = 1 if _8bit_imm else vm.operand_size

        RM, R = vm.process_ModRM(sz, sz)

        imm = vm.mem.get(vm.eip, imm_sz)
        vm.eip += imm_sz

        type, loc, _ = RM

        src1 = to_int(imm, True)
        src2 = to_int((vm.mem if type else vm.reg).get(loc, sz), True)

        tmp_xp = (src1 * src2).to_bytes(sz * 2, byteorder, signed=True)

        set_flags = sign_extend(tmp_xp[:sz], sz * 2) != tmp_xp

        vm.reg.eflags_set(Reg32.OF, set_flags)
        vm.reg.eflags_set(Reg32.CF, set_flags)

        vm.reg.set(R[1], tmp_xp[:sz])

        logger.debug('imul %s, %s=%d, imm%d=%d',
                     reg_names[R[1]][sz],
                     hex(loc) if type else reg_names[loc][sz],
                     src2, sz * 8, src1)

        # if debug: print('imul r{1}, {0}{1}, imm{1}'.format('m' if type else '_r', sz * 8))
        return True
