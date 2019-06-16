from ..util import Instruction, byteorder

from functools import partialmethod as P

import logging
logger = logging.getLogger(__name__)


class FLD(Instruction):
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
        RM, R = vm.process_ModRM(sz)

        _, loc, _ = RM

        flt80 = vm.mem.get_float_eip(loc, bits)

        vm.fpu.push(flt80)

        logger.debug('fld%d 0x%08x = %s', bits // 8, loc, flt80)

        return True

    def m_st(vm, i: int):
        raise RuntimeError("Can't load from ST yet!")

        sz = vm.freg.allowed_sizes[0]
        tmp = vm.freg.registers[-sz * (i + 1): -sz * i]

        vm.freg.registers[:sz] = tmp

        return True


# FST / FSTP
class FST(Instruction):
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

        RM, R = vm.process_ModRM(vm.operand_size)
        _, loc, _ = RM

        data = vm.fpu.ST(0)

        vm.mem.set_float(loc, bits // 8, data)

        if R[1] == 2:
            logger.debug('fst 0x%08x := %s', loc, data)
        else:
            vm.fpu.pop()
            logger.debug('fstp 0x%08x := %s', loc, data)

        return True

    def st(vm, i: int, do_pop: bool):
        raise RuntimeError("Can't store to ST yet")
        old_eip = vm.eip

        sz = vm.operand_size
        RM, R = vm.process_ModRM(sz, sz)
        type, loc, _ = RM

        #_sz = vm.freg.allowed_sizes[0]
        data = vm.freg.ST0#registers[:_sz]  # get ST(0)

        #getattr(self, f"")
        #vm.freg.registers[(i & 0b111) * _sz: ((i + 1) & 0b111) * _sz] = data

        if do_pop:
            vm.freg.pop()

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

        RM, R = vm.process_ModRM(0)
        _, loc, _ = RM

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


# FADD
class FADD(Instruction):
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

# FDIV
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

    def fdiv(vm, i: int, reverse: bool):
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

    def fdivp(vm, i: int):
        res = vm.fpu.div(i, 0)
        vm.fpu.pop()

        logger.debug('fdivp ST(%d), ST(0) (ST(%d) := %s)', i, i + 1, res)

        return True


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

        RM, R = vm.process_ModRM(vm.operand_size)

        _, loc, _ = RM
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

        RM, R = vm.process_ModRM(vm.operand_size)

        _, loc, _ = RM
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

        logger.debug('fxch ST(%d)', i)

        # also set C1 to 0
        return True
