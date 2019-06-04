from ..util import Instruction, SegmentRegs

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

        # TODO: this should actually use segment registers!
        self.mem.segment_override = SegmentRegs.ES
        self.mem.set(edi, sz, eax)
        self.mem.segment_override = SegmentRegs.DS

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

        if ecx == 0:
            # do not execute, just skip
            if opcode in (0xa4, 0xa5, 0xaa, 0xab):  # movsd, movsw/movsd, stosb, stosw/stosd
                self.eip += 1
            else:
                raise ValueError(f'REP will not run: unknown opcode: {opcode:02x}')

            return True

        logger.debug('rep ecx=%d, opcode=0x%02x', ecx, opcode)

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
