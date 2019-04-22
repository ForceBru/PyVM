from ..debug import *
from ..util import Instruction, byteorder

from functools import partialmethod as P
import struct  # for float packing/unpacking

import logging
logger = logging.getLogger(__name__)

__fmt = {'little': '<', 'big': '>'}[byteorder]
FPACK32 = struct.Struct(__fmt + 'f')
FPACK64 = struct.Struct(__fmt + 'd')


def ConvertToDoubleExtendedPrecisionFP(SRC: bytes) -> bytes:
    if len(SRC) == FPACK64.size:
        return SRC

    unp, = FPACK32.unpack(SRC)
    return FPACK64.pack(unp)


def DoubleToFloat(SRC: bytes) -> bytes:
    flt, = FPACK64.unpack(SRC)
    return FPACK32.pack(flt)


class FLD(Instruction):
    def __init__(self):
        self.opcodes = {
            0xD9: P(self.m_fp, bits=32),
            0xDD: P(self.m_fp, bits=64),
            # 0xDB: P(self.m_fp, bits=80),
            **{
                0xD9C0 + i: P(self.m_st, i=i)
                for i in range(8)
            }
        }

    def m_fp(vm, bits: int):
        old_eip = vm.eip

        sz = vm.operand_size
        RM, R = vm.process_ModRM(sz, sz)

        if bits in (32, 64):
            if R[1] != 0:
                vm.eip = old_eip
                return False
        else:
            if R[1] != 5:
                vm.eip = old_eip
                return False

        type, loc, _ = RM

        _data = (vm.mem if type else vm.reg).get(loc, bits // 8)

        data = ConvertToDoubleExtendedPrecisionFP(_data)

        flt, = (FPACK32 if bits == 32 else FPACK64).unpack(_data)
        logger.debug('fld%d %s == %f', bits // 8, data.hex(), flt)
        # if debug:
        # flt, = (FPACK32 if bits == 32 else FPACK64).unpack(_data)
        # print(f"fld{bits//8} {data} ({flt})")

        vm.freg.push(data)

        return True

    def m_st(vm, i: int):
        raise RuntimeError("Can't load from ST yet!")

        sz = vm.freg.allowed_sizes[0]
        tmp = vm.freg.registers[-sz * (i + 1): -sz * i]

        vm.freg.registers[:sz] = tmp

        return True


# FST / FSTP / FIST / FISTP
class FST(Instruction):
    def __init__(self):
        self.opcodes = {
            0xD9: P(self.m_fp, bits=32),  # fst m32fp / fstp32fp
            0xDD: P(self.m_fp, bits=64),  # fst m64fp / fstp64fp
            # 0xDB: P(self.m_fp, bits=80),
            **{
                0xDDD0 + i: P(self.st, i=i, pop=False)
                for i in range(8)
            },
            **{
                0xDDD8 + i: P(self.st, i=i, pop=True)
                for i in range(8)
            },

            0xDF: P(self.m_int, bits=0),  # fistp (m16int / m64int)
            0xDB: P(self.m_int, bits=32), # fistp m32int
        }

    def m_fp(vm, bits: int):
        old_eip = vm.eip

        RM, R = vm.process_ModRM(vm.operand_size)
        type, loc, _ = RM

        # _sz = vm.freg.allowed_sizes[0]
        # data = vm.freg.registers[:_sz]  # get ST(0)

        if R[1] == 2:
            data = vm.freg.ST0
            if bits == 32:
                data = DoubleToFloat(data)

            logger.debug('fst 0x%x := %s', loc, data[:bits // 8].hex())
            # if debug: print(f"fst {data} -> 0x{loc:02X}")
            (vm.mem if type else vm.reg).set(loc, data[:bits // 8])
        elif R[1] == 3:
            data = vm.freg.ST0
            if bits == 32:
                data = DoubleToFloat(data)

            logger.debug('fstp 0x%x := %s', loc, data[:bits // 8].hex())
            # if debug: print(f"fstp {data} -> 0x{loc:02X}")
            (vm.mem if type else vm.reg).set(loc, data[:bits // 8])
            vm.freg.pop()  # TOP may not equal 0
        else:
            vm.eip = old_eip
            return False

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

    def m_int(vm, bits: int):
        old_eip = vm.eip

        RM, R = vm.process_ModRM(vm.operand_size)

        do_pop = None
        if bits == 0:
            if R[1] == 2:
                bits, do_pop = 16, False
            elif R[1] == 3:
                bits, do_pop = 16, True
            elif R[1] == 7:
                bits, do_pop = 64, True
            else:
                return False
        else:
            if R[1] == 2:
                do_pop = False
            elif R[1] == 3:
                do_pop = True
            else:
                return False

        assert do_pop is not None

        logger.debug('fistp 0x%x (ctrl=0x%x)', -1, vm.freg.control)
        # if debug: print("{} 0x{:02x} (ctrl={:019_b})".format('fistp', -1, vm.freg.control))

        ST0 = vm.freg.ST0
        ST0, = FPACK64.unpack(ST0)

        ST0_int = int(ST0)

        #print(f"FISTP Got float: {ST0}")

        type, loc, _ = RM
        (vm.mem if type else vm.reg).set(loc, ST0_int.to_bytes(bits // 8, byteorder))

        if do_pop:
            vm.freg.pop()

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

    def fmulp(vm, i: int):
        _SRC, _DST = vm.freg._get_st(i), vm.freg.ST0

        SRC, = FPACK64.unpack(_SRC)
        DST, = FPACK64.unpack(_DST)

        RET = SRC * DST

        logger.debug('fmulp (%s == %f), (%s == %f)', _DST.hex(), DST, _SRC.hex(), SRC)
        # if debug: print(f"fmulp {_SRC}({SRC}) * {_DST}({DST}) = {RET}")

        vm.freg._set_st(i, FPACK64.pack(RET))
        vm.freg.pop()

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

    def faddp(vm, i: int):
        _SRC, _DST = vm.freg._get_st(i), vm.freg.ST0

        # if debug: print(f"Add: {_SRC} + {_DST}")

        SRC, = FPACK64.unpack(_SRC)
        DST, = FPACK64.unpack(_DST)

        RET = SRC + DST

        logger.debug('faddp (%s == %f), (%s == %f)', _SRC.hex(), SRC, _DST.hex(), DST)
        if debug: print(f"Add result: {RET}")

        vm.freg._set_st(i, FPACK64.pack(RET))
        vm.freg.pop()

        return True

# FDIV
class FDIV(Instruction):
    def __init__(self):
        self.opcodes = {
            **{
                0xDEF8 + i: P(self.fdivp, i=i)
                for i in range(8)
            },
            **{
                0xD8F0 + i: P(self.fdiv, i=i, reverse=False)
                for i in range(8)
            }
        }

    def fdiv(vm, i: int, reverse: bool):
        """
        Divide register by register.
        :param i:
        :param reverse: If `False`, compute ST0 = ST0 / STi, otherwise STi = STi / ST0
        :return:
        """

        STi, ST0 = vm.freg._get_st(i), vm.freg.ST0

        STi, = FPACK64.unpack(STi)
        ST0, = FPACK64.unpack(ST0)

        if debug: print("Dividing ST{} ({}) by ST{} ({})".format(0 if not reverse else i,
                                                             ST0 if not reverse else STi,
                                                             0 if reverse else i,
                                                             ST0 if reverse else STi,
                                                             ), end='')

        RET = (ST0 / STi) if not reverse else (STi / ST0)
        if debug: print(f' = {RET}')
        RET = FPACK64.pack(RET)

        vm.freg._set_st(0 if not reverse else i, RET)

        return True


    def fdivp(vm, i: int):
        SRC, DST = vm.freg._get_st(i), vm.freg.ST0

        if debug: print(f"Div: {SRC} / {DST}")

        SRC, = FPACK64.unpack(SRC)
        DST, = FPACK64.unpack(DST)

        RET = SRC / DST
        if debug: print(f"Div  result: {RET}")

        vm.freg._set_st(i, FPACK64.pack(RET))
        vm.freg.pop()

        return True


class FLDCW(Instruction):
    def __init__(self):
        self.opcodes = {
            0xD9: self.m2byte
        }

    def m2byte(vm):
        old_eip = vm.eip

        RM, R = vm.process_ModRM(vm.operand_size)

        if R[1] != 5:
            vm.eip = old_eip
            return False

        type, loc, _ = RM
        control = (vm.mem if type else vm.reg).get(loc, 2)
        vm.freg.control = int.from_bytes(control, byteorder)

        if debug: print("{} 0x{:02x} (ctrl={:019_b})".format('fldcw', loc, vm.freg.control))

        return True


# FSTCW/FNSTCW
class FSTCW(Instruction):
    def __init__(self):
        self.opcodes = {
            0xD9: P(self.m2byte, check=False),
            0x9BD9: P(self.m2byte, check=True)
        }

    def m2byte(vm, check: bool):
        old_eip = vm.eip

        RM, R = vm.process_ModRM(vm.operand_size)

        if R[1] != 7:
            vm.eip = old_eip
            return False

        type, loc, _ = RM

        if debug: print("{} 0x{:02x} (ctrl={:019_b})".format('fstcw' if check else 'fnstcw', loc, vm.freg.control))
        control = vm.freg.control.to_bytes(2, byteorder)
        (vm.mem if type else vm.reg).set(loc, control)

        return True

# FXCH
class FXCH(Instruction):
    def __init__(self):
        self.opcodes = {
            0xD9C8 + i: P(self.fxch, i=i)
            for i in range(8)
        }

    def fxch(vm, i: int):
        if debug: print(f'fxch ST{i}')
        STi, ST0 = vm.freg._get_st(i), vm.freg.ST0

        tmp = ST0
        vm.freg.ST0 = STi
        vm.freg._set_st(i, tmp)

        # also set C1 to 0
        return True