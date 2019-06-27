from ..util import Instruction, SegmentRegs

from functools import partialmethod as P

if __debug__:
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

    def m(vm, _8bit: bool) -> True:
        sz = 1 if _8bit else vm.operand_size

        eax = vm.reg.get(0, sz)
        edi = vm.reg.get(7, vm.address_size)

        vm.mem.segment_override = SegmentRegs.ES
        vm.mem.set(edi, sz, eax)
        vm.mem.segment_override = SegmentRegs.DS

        if not vm.reg.eflags.DF:
            edi += sz
        else:
            edi -= sz

        edi &= MAXVALS[vm.address_size]

        vm.reg.set(7, vm.address_size, edi)

        if __debug__:
            logger.debug(
                'stos%s [0x%x], eax=0x%x',
                'b' if sz == 1 else ('w' if sz == 2 else 'd'), edi, eax
            )

        return True


class REP(Instruction):
    def __init__(self):
        self.opcodes = {
            0xF3: self.m
        }

    def m(vm) -> True:
        opcode = vm.mem.get(vm.eip, 1)
        orig_eip = vm.eip

        sz = vm.address_size

        ecx = vm.reg.get(1, sz)

        if ecx == 0:
            # do not execute, just skip
            if opcode in {0xa4, 0xa5, 0xaa, 0xab}:  # movsd, movsw/movsd, stosb, stosw/stosd
                vm.eip += 1
            else:
                raise ValueError(f'REP will not run: unknown opcode: {opcode:02x}')

            return True

        logger.debug('rep ecx=%d, opcode=0x%02x', ecx, opcode)

        while ecx != 0:
            ecx -= 1

            # repeatedly read the next opcode and execute it
            vm.opcode = opcode
            vm.execute_opcode()

            if ecx == 0:
                break

            vm.eip = orig_eip

        vm.reg.set(1, sz, ecx)
        return True
