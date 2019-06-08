import logging
from functools import partialmethod as P
from unittest.mock import MagicMock

from ..debug import reg_names
from ..util import Instruction, to_int, to_signed, byteorder

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
        logger.debug('nop')

        return True

    def rm(vm) -> True:
        vm.process_ModRM(vm.operand_size)

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
JP  = compile('vm.reg.eflags.PF', 'p', 'eval')
JNP  = compile('not vm.reg.eflags.PF', 'np', 'eval')
JL   = compile('vm.reg.eflags.SF != vm.reg.eflags.OF', 'l', 'eval')
JNL  = compile('vm.reg.eflags.SF == vm.reg.eflags.OF', 'nl', 'eval')
JLE  = compile('vm.reg.eflags.ZF or vm.reg.eflags.SF != vm.reg.eflags.OF', 'ng', 'eval')
JNLE   = compile('not vm.reg.eflags.ZF and vm.reg.eflags.SF == vm.reg.eflags.OF', 'g', 'eval')

JUMPS = [JO, JNO, JB, JNB, JZ, JNZ, JBE, JNBE, JS, JNS, JP, JNP, JL, JNL, JLE, JNLE]

JCXZ = compile('not vm.reg.get(0, sz)', 'cxz', 'eval')


class JMP(Instruction):
    """
        Jump to a memory address.

        Operation:
            EIP = memory_location
    """

    def __init__(self):
        self.opcodes = {
            0xEB: P(self.rel, _8bit=True),
            0xE9: P(self.rel, _8bit=False),

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

    def rel(vm, _8bit, jump=compile('True', 'jump', 'eval')) -> True:
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

        logger.debug('j%s rel%d 0x%08x', jump.co_filename, sz * 8, vm.eip)
        
        return True

    def rm_m(vm) -> bool:
        old_eip = vm.eip

        sz = vm.operand_size
        RM, R = vm.process_ModRM(sz, sz)

        if R[1] == 4:  # this is jmp r/m
            type, loc, _ = RM

            tmpEIP = (vm.mem if type else vm.reg).get(loc, vm.address_size) 
                      
            vm.eip = tmpEIP & MAXVALS[vm.address_size]

            assert vm.eip < vm.mem.size

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
        RM, R = vm.process_ModRM(1)  # we know it's 1 byte

        type, loc, _ = RM

        byte = int(eval(cond))
        (vm.mem if type else vm.reg).set(loc, 1, byte)

        logger.debug('set%s %s := %d', cond.co_filename, hex(loc) if type else reg_names[loc][1], byte)

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

        RM, R = vm.process_ModRM(sz)

        if not eval(cond):
            return True

        type, loc, _ = RM

        data = (vm.mem if type else vm.reg).get(loc, sz)

        vm.reg.set(R[1], sz, data)

        logger.debug('cmov%s %s, %s=0x%x', cond.co_filename, reg_names[R[1]][sz], hex(loc) if type else reg_names[loc][sz], data)

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

        RM, R = vm.process_ModRM(sz)
        type, loc, _ = RM

        base = (vm.mem if type else vm.reg).get(loc, sz)
        offset = vm.reg.get(R[1], sz)

        logger.debug('bt %s, 0x%02x', hex(loc) if type else reg_names[loc][sz], offset)

        if type == 0:  # first arg is a register
            offset %= sz * 8

        vm.reg.eflags.CF = (base >> offset) & 1

        return True

    def rm_imm(vm) -> bool:
        sz = vm.operand_size

        RM, R = vm.process_ModRM(sz)
        type, loc, _ = RM

        if R[1] != 4:  # this is not bt
            return False

        if type == 1:
            base = vm.mem.get(loc, 1)  # read ONE BYTE
        else:
            base = vm.reg.get(loc, sz)

        offset = vm.mem.get_eip(vm.eip, 1)  # always 8 bits
        vm.eip += 1

        logger.debug('bt %s, 0x%02x', hex(loc) if type else reg_names[loc][sz], offset)

        if type == 0:  # first arg is a register
            offset %= sz * 8

        vm.reg.eflags.CF = (base >> offset) & 1

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
        #imm = to_int(imm)
        vm.eip += 1

        vm.interrupt(imm)

        logger.debug('int 0x%x', imm)

        return True

####################
# CALL
####################
CALL_DEPTH = 0
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
        RM, R = vm.process_ModRM(sz, sz)
        
        if R[1] == 2:  # this is call r/m
            type, loc, size = RM

            data = (vm.mem if type else vm.reg).get(loc, size)
          
            tmpEIP = data & MAXVALS[sz]
          
            # TODO: check whether tmpEIP is OK
          
            vm.stack_push(vm.eip)
          
            vm.eip = tmpEIP

            logger.debug('call %s=0x%x => 0x%x', hex(loc) if type else reg_names[loc][sz], data, vm.eip)
            # if debug: print(f'call {hex(loc) if type else reg_names[loc][sz]}={bytes(data)} => {hex(vm.eip)}')

            return True
        elif R[1] == 3:  # this is call m
            vm.eip = old_eip
            return False

        vm.eip = old_eip
        return False

    def rel(vm) -> True:
        sz = vm.operand_size
        dest = vm.mem.get(vm.eip, sz)
        vm.eip += sz
        dest = to_signed(dest, sz)
        tmpEIP = vm.eip + dest

        '''
        test = {
            0x000008BD: 'printf_core',
            0x0000050C: 'printf',
            0x00000760: 'vprintf',
            0x0000225e: 'pop_arg',
            0x000023E8: '__fwritex [MUST WRITE]',
            0x00006C08: '__memcpy_fwd',
            0x00002618: '__towrite',
            0x00000530: 'scanf',
            0x00002974: 'vscanf',
            0x00002A38: '__isoc99_vfscanf',
            0x00004A70: '__shlim',
            0x00004BA0: '__shgetc',
            0x00004C90: '__uflow',
            0x00004CD4: '__toread',
            0x000004E0: '__vsyscall',
            0x000004F6: 'fcn.000004f6',
            0x000005D0: '__syscall_ret',
            0x00004D40: '__intscan',
            0x000005B8: '___errno_location',
            0x0000049F: 'exit',
            0x0000047C: 'dummy_1',
            0x0000047D: 'libc_exit_fini',
            0x00002668: '__stdio_exit',
            0x000026A8: '__stdio_exit.close_file',
            0x000006B4: '__stdio_write',
            0x000026FC: '__ofl_lock',
            0x00006E34: '__lock'
        }

        global CALL_DEPTH
        if tmpEIP in test:
            print('  ' * CALL_DEPTH + f'Calling {test[tmpEIP]} (0x{tmpEIP:08X}) @ 0x{vm.eip:08X}')
            if '__fwritex' in test[tmpEIP]:
                import struct
                s, l, f = struct.unpack('<3I', vm.stack_get(4 + 4 + 4))
                stri = vm.mem.get(s, l).decode()
                print(f'Args: (char *s={stri!r}, size_t l={l}, FILE *f=0x{f:08X})')
        else:
            print('  ' * CALL_DEPTH + f'Calling 0x{tmpEIP:08X}')

        CALL_DEPTH += 1
        '''

        assert tmpEIP < vm.mem.size

        vm.stack_push(vm.eip)
        vm.eip = tmpEIP

        logger.debug('call 0x%x => 0x%x', dest, vm.eip)
        # if debug: print(f'call {hex(dest)} => {hex(vm.eip)}')

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
        #eip_old = vm.eip - 1
        vm.eip = to_signed(vm.stack_pop(sz), sz)

        assert vm.eip < vm.mem.size
        '''
        global CALL_DEPTH
        eax = to_int(vm.reg.get(0, 4), True)
        print('  ' * CALL_DEPTH + f'Return {eax} to 0x{vm.eip:08X} from 0x{eip_old:08X}')
        CALL_DEPTH -= 1
        '''

        logger.debug('ret 0x%x', vm.eip)
        # if debug: print("ret (eip=0x{:02x})".format(vm.eip))

        return True

    def near_imm(vm) -> True:
        sz = 2  # always 16 bits
        vm.eip = to_int(vm.stack_pop(sz), True)

        imm = to_int(vm.mem.get(vm.eip, sz))
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

        vm.reg.set(5, (FrameTemp & MAXVALS[vm.operand_size]).to_bytes(4, byteorder))  # EBP
        esp = to_int(vm.reg.get(4, vm.operand_size)) - AllocSize
        vm.reg.set(4, esp.to_bytes(4, byteorder))

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

    def leave(self) -> True:
        """
        High-level procedure exit.

        Operation:
            1) ESP <- EBP
            2) EBP = stack_pop()
        """
        ESP, EBP = 4, 5  # depends on 'self.address_size' and 'self.operand_size'

        self.reg.set(ESP, self.address_size, self.reg.get(EBP, self.address_size))
        self.reg.set(EBP, self.operand_size, self.stack_pop(self.operand_size))

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

    def cpuid(self) -> True:
        """
        See: https://en.wikipedia.org/wiki/CPUID
        """
        eax, ebx, ecx, edx = 0, 3, 1, 2
        max_input_value = 0x01
        EAX_val = self.reg.get(eax, 4)

        if EAX_val == 0x00:
            self.reg.set(eax, max_input_value.to_bytes(4, byteorder))
            self.reg.set(ebx, b'Genu')
            self.reg.set(edx, b'ineI')
            self.reg.set(ecx, b'ntel')
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
            EAX_val = 0b0000_0000_0000_0000_0000_0100_0001_0000
            EBX_val = 0
            ECX_val = 0  # no extra technologies available
            EDX_val = 0b0000_0000_0000_0000_1000_0000_0000_0001  # CMOV (bit 5), fpu (bit 0)

            self.reg.set(eax, EAX_val.to_bytes(4, byteorder))
            self.reg.set(ebx, EBX_val.to_bytes(4, byteorder))
            self.reg.set(ecx, ECX_val.to_bytes(4, byteorder))
            self.reg.set(edx, EDX_val.to_bytes(4, byteorder))
        else:
            raise RuntimeError(f'Unsupported EAX value for CPUID: 0x{EAX_val:08X}')

        return True

####################
# HLT
####################
class HLT(Instruction):
    def __init__(self):
        self.opcodes = {
            0xF4: self.hlt
        }

    def hlt(self):
        raise RuntimeError(f'HALT @ 0x{self.eip:08X}')
