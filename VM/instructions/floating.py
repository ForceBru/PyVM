from functools import partialmethod as P
from unittest.mock import MagicMock

from ..util import Instruction

import logging
logger = logging.getLogger(__name__)


class FLD(Instruction):
    m_st = MagicMock(return_value=False)

    def __init__(self):
        self.opcodes = {
            0xD9: P(self.m_fp, bits=32, REG=0),
            0xDD: P(self.m_fp, bits=64, REG=0),
            0xDB: P(self.m_fp, bits=80, REG=5),
            **{
                0xD9C0 + i: P(self.m_st, i=i)
                for i in range(8)
            }
        }

    def m_fp(vm, bits: int, REG: int):
        ModRM = vm.mem.get_eip(vm.eip, 1)
        _REG = (ModRM & 0b00111000) >> 3

        if _REG != REG:
            return False

        sz = vm.operand_size
        
        RM, R = vm.process_ModRM()
        _, loc = RM

        flt80 = vm.mem.get_float(loc, bits)

        vm.fpu.push(flt80)

        logger.debug('fld%d 0x%08x = %s', bits // 8, loc, flt80)

        return True


# FST / FSTP
class FST(Instruction):
    st = MagicMock(return_value=False)

    def __init__(self):
        self.opcodes = {
            0xD9: [
                P(self.m_fp, bits=32, REG=2),    # FST m32fp
                P(self.m_fp, bits=32, REG=3),    # FSTP m32fp
            ],
            0xDD: [
                P(self.m_fp, bits=64, REG=2),    # FSTP m32fp
                P(self.m_fp, bits=64, REG=3),    # FSTP m64fp
            ],
            0xDB: P(self.m_fp, bits=80, REG=7),  # FSTP m80fp

            **{
                0xDDD0 + i: P(self.st, i=i, pop=False)
                for i in range(8)
            },
            **{
                0xDDD8 + i: P(self.st, i=i, pop=True)
                for i in range(8)
            }
        }

    def m_fp(vm, bits: int, REG: int):
        ModRM = vm.mem.get_eip(vm.eip, 1)
        _REG = (ModRM & 0b00111000) >> 3

        if _REG != REG:
            return False

        sz = vm.operand_size
        
        RM, R = vm.process_ModRM()
        _, loc = RM

        data = vm.fpu.ST(0)

        vm.mem.set_float(loc, bits // 8, data)

        if R[1] == 2:
            logger.debug('fst 0x%08x := %s', loc, data)
        else:
            vm.fpu.pop()
            logger.debug('fstp 0x%08x := %s', loc, data)

        return True


# FIST / FISTP
class FIST(Instruction):
    def __init__(self):
        self.opcodes = {
            0xDF: [
                P(self.fist, size=2, REG=2),  # FIST m16int
                P(self.fist, size=2, REG=3),  # FISTP m16int
                P(self.fist, size=8, REG=7),  # FISTP m64int
            ],
            0xDB: [
                P(self.fist, size=4, REG=2),  # FIST m32int
                P(self.fist, size=4, REG=3),  # FISTP m32int
            ]
        }

    def fist(vm, size: int, REG: int) -> bool:
        ModRM = vm.mem.get_eip(vm.eip, 1)
        _REG = (ModRM & 0b00111000) >> 3

        if _REG != REG:
            return False

        RM, R = vm.process_ModRM()
        _, loc = RM

        SRC = int(vm.fpu.ST(0))

        vm.mem.set(loc, size, SRC)

        if REG != 2:
            vm.fpu.pop()
            logger.debug('fistp 0x%08x := %d', loc, SRC)
        else:
            logger.debug('fist 0x%08x := %d', loc, SRC)

        return True


# FMUL/FMULP/FIMUL
class FMUL(Instruction):
    def __init__(self):
        self.opcodes = {
            **{
                0xDEC8 + i: P(self.fmulp, i=i)
                for i in range(8)
            }
        }

    def fmulp(vm, i: int) -> True:
        res = vm.fpu.mul(i, 0)
        vm.fpu.pop()

        logger.debug('fmulp (ST(%d) = %s)', i + 1, res)

        return True


# FADDP
class FADDP(Instruction):
    def __init__(self):
        self.opcodes = {
            **{
                0xDEC0 + i: P(self.faddp, i=i)
                for i in range(8)
            }
        }

    def faddp(vm, i: int) -> True:
        res = vm.fpu.add(i, 0)

        logger.debug('faddp ST(%d), ST(0) (ST(%d) := %s)', i, i + 1, res)

        vm.fpu.pop()

        return True


# FDIV/FDIVP
class FDIV(Instruction):
    def __init__(self):
        self.opcodes = {
            **{
                0xD8F0 + i: P(self.fdiv, i=i, reverse=True)
                for i in range(8)
            },
            **{
                0xDCF8 + i: P(self.fdiv, i=i, reverse=False)
                for i in range(8)
            },

            **{
                0xDEF8 + i: P(self.fdivp, i=i)
                for i in range(8)
            },
        }

    def fdiv(vm, i: int, reverse: bool) -> True:
        """
        Divide register by register.
        :param i:
        :param reverse: If `False`, compute ST0 = ST0 / STi, otherwise STi = STi / ST0
        :return:
        """
        if reverse:
            res = vm.fpu.div(0, i)
            logger.debug('fdiv ST(0), ST(%d) (ST(0) := %s)', i, res)
        else:
            res = vm.fpu.div(i, 0)
            logger.debug('fdiv ST(%d), ST(0) (ST(%d) := %s)', i, i, res)

        return True

    def fdivp(vm, i: int) -> True:
        res = vm.fpu.div(i, 0)
        vm.fpu.pop()

        logger.debug('fdivp ST(%d), ST(0) (ST(%d) := %s)', i, i + 1, res)

        return True


# FUCOM/FUCOMP/FUCOMPP/FCOMI/FCOMIP/FUCOMIP/FUCOMIPP
class FCOMP(Instruction):
    def __init__(self):
        self.opcodes = {
            # F*COM*
            **{
                0xD0E0 + i: P(self.fucom, pop=0, i=i, set_eflags=False)
                for i in range(8)
            },
            **{
                0xDDE8 + i: P(self.fucom, pop=1, i=i, set_eflags=False)
                for i in range(8)
            },
            0xDAE9: P(self.fucom, pop=2, i=1, set_eflags=False),

            # FCOMI
            **{
                0xDBF0 + i: P(self.fcom, pop=0, i=i, set_eflags=True)
                for i in range(8)
            },

            # FCOMIP
            **{
                0xDFF0 + i: P(self.fcom, pop=1, i=i, set_eflags=True)
                for i in range(8)
            },

            # FUCOMI
            **{
                0xDBE8 + i: P(self.fucom, pop=0, i=i, set_eflags=True)
                for i in range(8)
            },

            # FUCOMIP
            **{
                0xDFE8 + i: P(self.fucom, pop=1, i=i, set_eflags=True)
                for i in range(8)
            },
        }

    def fucom(vm, pop: int, i: int, set_eflags: bool) -> True:
        # Vol. 2A FUCOM/FUCOMP/FUCOMPP—Unordered Compare Floating Point Values
        # TODO: this should raise some exception or something?

        ST0, STi = vm.fpu.ST(0), vm.fpu.ST(i)

        if ST0 > STi:
            flags = 0, 0, 0
        elif ST0 < STi:
            flags = 0, 0, 1
        elif ST0 == STi:
            flags = 1, 0, 0
        else:
            # unordered
            flags = 1, 1, 1

        if set_eflags:
            vm.reg.eflags.ZF, vm.reg.eflags.PF, vm.reg.eflags.CF = flags
        else:
            vm.fpu.status.C3, vm.fpu.status.C2, vm.fpu.status.C0 = flags

        for _ in range(pop):
            vm.fpu.pop()

        return True

    def fcom(vm, pop: int, i: int, set_eflags: bool) -> True:
        ST0, STi = vm.fpu.ST(0), vm.fpu.ST(i)

        if ST0 > STi:
            flags = 0, 0, 0
        elif ST0 < STi:
            flags = 0, 0, 1
        elif ST0 == STi:
            flags = 1, 0, 0
        else:
            # unordered
            flags = 1, 1, 1

        if set_eflags:
            vm.reg.eflags.ZF, vm.reg.eflags.PF, vm.reg.eflags.CF = flags
        else:
            vm.fpu.status.C3, vm.fpu.status.C2, vm.fpu.status.C0 = flags

        for _ in range(pop):
            vm.fpu.pop()

        return True

# FLDCW
class FLDCW(Instruction):
    def __init__(self):
        self.opcodes = {
            0xD9: self.m2byte
        }

    def m2byte(vm, REG=5) -> bool:
        ModRM = vm.mem.get_eip(vm.eip, 1)
        _REG = (ModRM & 0b00111000) >> 3

        if _REG != REG:
            return False

        RM, R = vm.process_ModRM()
        _, loc = RM
        
        control = vm.mem.get(loc, 2)
        vm.fpu.control.value = control

        logger.debug('fldcw 0x%08x := %04x', loc, control)

        return True


# FSTCW/FNSTCW
class FSTCW(Instruction):
    def __init__(self):
        self.opcodes = {
            0xD9: P(self.m2byte, check=False),
            0x9BD9: P(self.m2byte, check=True)
        }

    def m2byte(vm, check: bool, REG=7) -> bool:
        ModRM = vm.mem.get_eip(vm.eip, 1)
        _REG = (ModRM & 0b00111000) >> 3

        if _REG != REG:
            return False

        sz = vm.operand_size
        RM, R = vm.process_ModRM()
        _, loc = RM
        
        vm.mem.set(loc, 2, vm.fpu.control.value)

        if check:
            # TODO: add check? WTF?
            logger.debug('fstcw 0x%08x := %02x', loc, vm.fpu.control.value)
        else:
            logger.debug('fnstcw 0x%08x := %02x', loc,  vm.fpu.control.value)

        return True


# FXCH
class FXCH(Instruction):
    def __init__(self):
        self.opcodes = {
            0xD9C8 + i: P(self.fxch, i=i)
            for i in range(8)
        }

    def fxch(vm, i: int) -> True:
        temp = vm.fpu.ST(0)
        vm.fpu.store(0, vm.fpu.ST(i))
        vm.fpu.store(i, temp)

        vm.fpu.status.C1 = 0

        logger.debug('fxch ST(%d)', i)

        return True
