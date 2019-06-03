from ..debug import *
from ..Registers import Reg32
from ..util import Instruction, to_int, byteorder,SegmentRegs
from ..misc import sign_extend, zero_extend

from functools import partialmethod as P

import logging
logger = logging.getLogger(__name__)

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

        edi = self.reg.get(7, self.address_size)

        #self.mem.set_seg(SegmentRegs.ES, edi, eax)
        # TODO: this should actually use segment registers!
        self.mem.set(edi, sz, eax)

        if not self.reg.eflags.DF:
            edi += sz
        else:
            edi -= sz

        edi &= MAXVALS[self.address_size]

        self.reg.set(7, self.address_size, edi)

        logger.debug('stos%s [0x%x], eax=0x%x', 'b' if sz == 1 else ('w' if sz == 2 else 'd'), edi, eax)

        return True


class REP(Instruction):
    def __init__(self):
        self.opcodes = {
            0xF3: self.m
        }

    def m(self) -> True:
        opcode = self.mem.get(self.eip, 1)
        orig_eip = self.eip

        sz = self.address_size

        ecx = self.reg.get(1, sz)

        while ecx != 0:
            ecx -= 1

            # repeatedly read the next opcode and execute it
            self.opcode = opcode
            self.execute_opcode()

            if ecx == 0:
                break

            self.eip = orig_eip

        self.reg.set(1, sz, ecx)
        return True
