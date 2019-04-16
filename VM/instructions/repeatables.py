from ..debug import *
from ..Registers import Reg32
from ..util import Instruction, to_int, byteorder
from ..misc import sign_extend, zero_extend

from functools import partialmethod as P


MAXVALS = [None, (1 << 8) - 1, (1 << 16) - 1, None, (1 << 32) - 1]  # MAXVALS[n] is the maximum value of an unsigned n-bit number
SIGNS   = [None, 1 << 8 - 1, 1 << 16 - 1, None, 1 << 32 - 1]  # SIGNS[n] is the maximum absolute value of a signed n-bit number

####################
# STOSB / STOSW / STOSD
####################
class STOS(Instruction):
    def __init__(self):
        self.opcodes = {
            0xAA: P(self.m, _8bit=True),
            0xAB: P(self.m, _8bit=False)
        }

    def m(self, _8bit: bool) -> True:
        sz = 1 if _8bit else self.operand_size

        eax = self.reg.get(0, sz)

        edi = to_int(self.reg.get(7, sz))  # should actually be DS:EDI

        self.mem.set(edi, eax)

        if not self.reg.eflags_get(Reg32.DF):
            edi += sz
        else:
            edi -= sz

        edi &= MAXVALS[sz]

        self.reg.set(7, edi.to_bytes(sz, byteorder))

        if debug: print('stos{}'.format('b' if sz == 1 else ('w' if sz == 2 else 'd')))
        return True


class REP(Instruction):
    def __init__(self):
        self.opcodes = {
            0xF3: P(self.m)
        }

    def m(self) -> True:
        opcode, = self.mem.get(self.eip, 1)
        orig_eip = self.eip

        sz = self.address_size

        ecx = to_int(self.reg.get(1, sz))

        while ecx != 0:
            ecx -= 1

            # repeatedly read the next opcode and execute it
            self.opcode = opcode
            self.execute_opcode()

            if ecx == 0:
                self.reg.set(1, ecx.to_bytes(sz, byteorder))
                return True

            self.eip = orig_eip

        self.reg.set(1, ecx.to_bytes(sz, byteorder))
        return True
