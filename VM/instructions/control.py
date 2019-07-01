from functools import partialmethod as P
from unittest.mock import MagicMock

from ..util import Instruction, to_int, to_signed, byteorder

if __debug__:
    from ..debug import debug_operand, debug_register_operand
    import logging
    logger = logging.getLogger(__name__)

MAXVALS = [None, (1 << 8) - 1, (1 << 16) - 1, None, (1 << 32) - 1]  # MAXVALS[n] is the maximum value of an unsigned n-byte number
SIGNS   = [None, 1 << 8 - 1, 1 << 16 - 1, None, 1 << 32 - 1]  # SIGNS[n] is the maximum absolute value of a signed n-byte number


class NOP(Instruction):
    def __init__(self):
        self.opcodes = {
            0x90: self.nop,
            0x0F1F: self.rm
        }

    def nop(vm) -> True:
        if __debug__:
            logger.debug('nop')

        return True

    def rm(vm) -> True:
        vm.process_ModRM()

        if __debug__:
            logger.debug('nop')

        return True


####################
# JMP
####################
JO   = compile('vm.reg.eflags.OF', 'o', 'eval')
JNO  = compile('not vm.reg.eflags.OF', 'no', 'eval')
JB   = compile('vm.reg.eflags.CF', 'b', 'eval')
JNB  = compile('not vm.reg.eflags.CF', 'nb', 'eval')
JZ   = compile('vm.reg.eflags.ZF', 'z', 'eval')
JNZ  = compile('not vm.reg.eflags.ZF', 'nz', 'eval')
JBE  = compile('vm.reg.eflags.CF or vm.reg.eflags.ZF', 'be', 'eval')
JNBE = compile('not vm.reg.eflags.CF and not vm.reg.eflags.ZF', 'nbe', 'eval')
JS   = compile('vm.reg.eflags.SF', 's', 'eval')
JNS  = compile('not vm.reg.eflags.SF', 'ns', 'eval')
JP   = compile('vm.reg.eflags.PF', 'p', 'eval')
JNP  = compile('not vm.reg.eflags.PF', 'np', 'eval')
JL   = compile('vm.reg.eflags.SF != vm.reg.eflags.OF', 'l', 'eval')
JNL  = compile('vm.reg.eflags.SF == vm.reg.eflags.OF', 'nl', 'eval')
JLE  = compile('vm.reg.eflags.ZF or vm.reg.eflags.SF != vm.reg.eflags.OF', 'le', 'eval')
JNLE = compile('not vm.reg.eflags.ZF and vm.reg.eflags.SF == vm.reg.eflags.OF', 'nle', 'eval')

JUMPS = [JO, JNO, JB, JNB, JZ, JNZ, JBE, JNBE, JS, JNS, JP, JNP, JL, JNL, JLE, JNLE]

_JMP = compile('True', 'mp', 'eval')
JCXZ = compile('not vm.reg.get(0, sz)', 'cxz', 'eval')


class JMP(Instruction):
    """
        Jump to a memory address.

        Operation:
            EIP = memory_location
    """

    def __init__(self):
        self.opcodes = {
            0xEB: P(self.rel, _8bit=True, jump=_JMP),
            0xE9: P(self.rel, _8bit=False, jump=_JMP),

            0xFF: self.rm_m,
            0xEA: P(self.ptr, _8bit=False),

            0xE3: P(self.rel, _8bit=True, jump=JCXZ),

            **{
                opcode: P(self.rel, _8bit=True, jump=JUMPS[opcode % 0x70])
                for opcode in range(0x70, 0x80)
            },

            **{
                opcode: P(self.rel, _8bit=False, jump=JUMPS[opcode % 0x0F80])
                for opcode in range(0x0F80, 0x0F90)
            }
        }

    def rel(vm, _8bit, jump) -> True:
        sz = 1 if _8bit else vm.operand_size

        d = vm.mem.get(vm.eip, sz, True)
        vm.eip += sz

        if not eval(jump):
            return True
            
        tmpEIP = vm.eip + d
        if vm.operand_size == 2:
          tmpEIP &= MAXVALS[vm.operand_size]
          
        assert tmpEIP < vm.mem.size

        vm.eip = tmpEIP

        if __debug__:
            logger.debug('j%s rel%d 0x%08x', jump.co_filename, sz * 8, vm.eip)
        
        return True

    def rm_m(vm) -> bool:
        old_eip = vm.eip

        sz = vm.operand_size
        RM, R = vm.process_ModRM()

        if R[1] == 4:  # this is jmp r/m
            type, loc = RM

            tmpEIP = (type).get(loc, vm.address_size) 
                      
            vm.eip = tmpEIP & MAXVALS[vm.address_size]

            assert vm.eip < vm.mem.size

            if __debug__:
                logger.debug('jmp rm%d 0x%x', sz * 8, vm.eip)

            return True
        elif R[1] == 5:  # this is jmp m
            segment_selector_address = to_int(vm.mem.get(vm.eip, vm.address_size), True)
            vm.eip += vm.address_size
            offset_address = to_int(vm.mem.get(vm.eip, vm.address_size), True)
            vm.eip += vm.address_size

            sz = 4 if vm.operand_size == 4 else 2

            segment_selector = to_int(vm.mem.get(segment_selector_address, 2), True)
            offset = to_int(vm.mem.get(offset_address, sz))

            tempEIP = offset

            assert vm.eip in vm.mem.bounds

            vm.reg.CS = segment_selector  # TODO: do something with CS

            if vm.operand_size == 4:
                vm.eip = tempEIP
            else:
                vm.eip = tempEIP & 0x0000FFFF

            if __debug__:
                logger.debug('jmp m%d 0x%x', sz * 8, vm.eip)

            return True

        vm.eip = old_eip
        return False

    def ptr(vm) -> True:
        segment_selector = to_int(vm.mem.get(vm.eip, 2), True)
        vm.eip += 2

        sz = 4 if vm.operand_size == 4 else 2
        offset = to_int(vm.mem.get(vm.eip, sz), True)
        vm.eip += sz

        tempEIP = offset

        assert vm.eip in vm.mem.bounds

        vm.reg.CS = segment_selector  # TODO: do something with CS

        if vm.operand_size == 4:
            vm.eip = tempEIP
        else:
            vm.eip = tempEIP & 0x0000FFFF

        if __debug__:
            logger.debug('jmp m%d 0x%x', sz * 8, vm.eip)

        return True


####################
# SETcc
####################
class SETcc(Instruction):
    def __init__(self):
        self.opcodes = {
            opcode: P(self.rm8, cond=JUMPS[opcode % 0x0F90])
            for opcode in range(0x0F90, 0x0FA0)
        }

    def rm8(vm, cond) -> True:
        sz = 1  # we know it's 1 byte
        RM, R = vm.process_ModRM()

        type, loc = RM

        byte = eval(cond)
        (type).set(loc, sz, byte)

        if __debug__:
            logger.debug('set%s %s := %d', cond.co_filename, debug_operand(RM, sz), byte)

        return True


####################
# CMOVcc
####################
class CMOVCC(Instruction):
    def __init__(self):
        self.opcodes = {
            opcode: P(self.r_rm, cond=JUMPS[opcode % 0x0F40])
            for opcode in range(0x0F40, 0x0F50)
        }

    def r_rm(vm, cond) -> True:
        sz = vm.operand_size

        RM, R = vm.process_ModRM()

        if not eval(cond):
            return True

        type, loc = RM

        data = (type).get(loc, sz)

        vm.reg.set(R[1], sz, data)

        if __debug__:
            logger.debug(
                'cmov%s %s, %s=0x%x',
                cond.co_filename,
                debug_operand(R, sz), debug_operand(RM, sz),
                data
            )

        return True


####################
# BT
####################
class BT(Instruction):
    def __init__(self):
        self.opcodes = {
            0x0FBA: self.rm_imm,
            0x0FA3: self.rm_r
        }

    def rm_r(vm) -> True:
        sz = vm.operand_size

        RM, R = vm.process_ModRM()
        _type, loc = RM

        base = (_type).get(loc, sz)
        offset = vm.reg.get(R[1], sz)

        if isinstance(_type, type(vm.reg)):
            offset %= sz * 8

        vm.reg.eflags.CF = (base >> offset) & 1

        if __debug__:
            logger.debug(
                'bt %s, 0x%02x',
                debug_operand(RM, sz),
                offset
            )

        return True

    def rm_imm(vm) -> bool:
        sz = vm.operand_size

        RM, R = vm.process_ModRM()
        _type, loc = RM

        if R[1] != 4:  # this is not bt
            return False

        if isinstance(_type, type(vm.mem)):
            base = vm.mem.get(loc, 1)  # read ONE BYTE
        else:
            base = vm.reg.get(loc, sz)

        offset = vm.mem.get_eip(vm.eip, 1)  # always 8 bits
        vm.eip += 1

        if isinstance(_type, type(vm.reg)):  # first arg is a register
            offset %= sz * 8

        vm.reg.eflags.CF = (base >> offset) & 1

        if __debug__:
            logger.debug(
                'bt %s, 0x%02x',
                debug_operand(RM, sz),
                offset
            )

        return True


####################
# INT
####################
class INT(Instruction):
    """
    Call to interrupt procedure.
    """

    def __init__(self):
        self.opcodes = {
            0xCC: self._3,
            0xCD: self.imm
            }

    def _3(vm) -> True:
        vm.descriptors[2].write("[!] It's a trap! (literally)")

        return True

    def imm(vm) -> True:
        imm = vm.mem.get_eip(vm.eip, 1)  # always 8 bits
        vm.eip += 1

        vm.interrupt(imm)

        if __debug__:
            logger.debug('int 0x%x', imm)

        return True


####################
# CALL
####################
class CALL(Instruction):
    """
    Call a procedure.
    """
    def __init__(self):
        self.opcodes = {
            0xE8: self.rel,
            0xFF: self.rm_m,
            0x9A: self.ptr
            }

    # TODO: implement far calls
    # rm_m = MagicMock(return_value=False)
    ptr = MagicMock(return_value=False)
    
    def rm_m(vm) -> bool:
        old_eip = vm.eip
        
        sz = vm.operand_size
        RM, R = vm.process_ModRM()
        
        if R[1] == 2:  # this is call r/m
            type, loc = RM

            data = (type).get(loc, sz)
          
            tmpEIP = data & MAXVALS[sz]
          
            # TODO: check whether tmpEIP is OK
          
            vm.stack_push(vm.eip)
          
            vm.eip = tmpEIP

            if __debug__:
                logger.debug(
                    'call %s=0x%08x => 0x%08x',
                    debug_operand(RM, sz),
                    data, vm.eip
                )

            return True
        elif R[1] == 3:  # this is call m
            vm.eip = old_eip
            return False

        vm.eip = old_eip
        return False

    def rel(vm) -> True:
        sz = vm.operand_size
        dest = vm.mem.get(vm.eip, sz, True)
        vm.eip += sz

        tmpEIP = vm.eip + dest

        vm.stack_push(vm.eip)
        vm.eip = tmpEIP

        if __debug__:
            logger.debug('call 0x%08x => 0x%08x', dest, vm.eip)

        return True


####################
# RET
####################
class RET(Instruction):
    """
    Return to calling procedure.
    """
    def __init__(self):
        self.opcodes = {
            0xC3: self.near,
            0xCB: self.far,

            0xC2: self.near_imm,
            0xCA: self.far_imm,
            }

    # TODO: implement far returns
    far = MagicMock(return_value=False)
    far_imm = MagicMock(return_value=False)

    def near(vm) -> True:
        sz = vm.operand_size
        vm.eip = to_signed(vm.stack_pop(sz), sz)

        if __debug__:
            logger.debug('ret 0x%08x', vm.eip)

        return True

    def near_imm(vm) -> True:
        raise NotImplementedError('This is not optimized yet!')

        sz = 2  # always 16 bits
        vm.eip = to_signed(vm.stack_pop(sz), sz)

        imm = vm.mem.get(vm.eip, sz)
        vm.eip += sz

        vm.stack_pop(imm)

        assert vm.eip in vm.mem.bounds

        logger.debug('ret 0x%x', vm.eip)

        return True


####################
# ENTER
####################
class ENTER(Instruction):
    def __init__(self):
        self.opcodes = {
            0xC8: self.enter
        }

    def enter(vm):
        AllocSize = vm.mem.get_eip(vm.eip, 2)
        vm.eip += 2

        NestingLevel = vm.mem.get_eip(vm.eip, 1) % 32
        vm.eip += 1

        ebp = vm.reg.get(5, vm.operand_size)
        vm.stack_push(ebp)
        FrameTemp = vm.reg.get(4, vm.operand_size)  # ESP

        if NestingLevel == 0:
            ...
        elif NestingLevel == 1:
            vm.stack_push(FrameTemp.to_bytes(vm.stack_address_size, byteorder))
        else:
            raise RuntimeError(f"Instruction 'enter {AllocSize}, {NestingLevel}' is not implemented yet")

        vm.reg.ebp = FrameTemp & MAXVALS[vm.operand_size]
        vm.reg.esp = vm.reg.get(4, vm.operand_size) - AllocSize

        if __debug__:
            logger.debug('enter 0x%04x, 0x%02x', AllocSize, NestingLevel)

        return True


####################
# LEAVE
####################
class LEAVE(Instruction):
    def __init__(self):
        self.opcodes = {
            0xC9: self.leave
            }

    def leave(vm) -> True:
        """
        High-level procedure exit.

        Operation:
            1) ESP <- EBP
            2) EBP = stack_pop()
        """
        ESP, EBP = 4, 5  # depends on 'self.address_size' and 'self.operand_size'

        vm.reg.set(ESP, vm.address_size, vm.reg.get(EBP, vm.address_size))
        vm.reg.set(EBP, vm.operand_size, vm.stack_pop(vm.operand_size))

        if __debug__:
            logger.debug('leave')

        return True


####################
# CPUID
####################
class CPUID(Instruction):
    def __init__(self):
        self.opcodes = {
            0x0FA2: self.cpuid
        }

    def cpuid(vm) -> True:
        """
        See: https://en.wikipedia.org/wiki/CPUID
        """
        eax, ebx, ecx, edx = 0, 3, 1, 2
        max_input_value = 0x01
        EAX_val = vm.reg.get(eax, 4)

        if EAX_val == 0x00:
            vm.reg.eax = max_input_value
            vm.reg.ebx = int.from_bytes(b'Genu', byteorder)
            vm.reg.edx = int.from_bytes(b'ineI', byteorder)
            vm.reg.ecx = int.from_bytes(b'ntel', byteorder)
        elif EAX_val == 0x01:
            # Processor Model, Family, Stepping in EAX (https://en.wikichip.org/wiki/intel/cpuid)
            # Family 3, core 80486DX
            #
            # Reserved: 0b0000
            # extended family: 0b0000_0000
            # extended model: 0b0000,
            # reserved + type: 0b0000 (original OEM processor),
            # family: 0b0100,
            # model: 0b0001,
            # stepping: 0b0000
            vm.reg.eax = 0b0000_0000_0000_0000_0000_0100_0001_0000
            vm.reg.ebx = 0
            vm.reg.ecx = 0
            vm.reg.edx = 0b0000_0000_0000_0000_1000_0000_0000_0001  # CMOV (bit 5), fpu (bit 0)
        else:
            raise RuntimeError(f'Unsupported EAX value for CPUID: 0x{EAX_val:08X}')

        if __debug__:
            logger.debug('cpuid')

        return True


####################
# HLT
####################
class HLT(Instruction):
    def __init__(self):
        self.opcodes = {
            0xF4: self.hlt
        }

    def hlt(vm):
        raise RuntimeError(f'HALT @ 0x{vm.eip - 1:08x}')  # Subtract 1 because EIP points to the NEXT opcode
