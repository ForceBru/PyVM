from ..debug import *
from ..Registers import Reg32
from ..util import Instruction, to_int, byteorder
from ..misc import sign_extend

from functools import partialmethod as P
from unittest.mock import MagicMock

MAXVALS = [None, (1 << 8) - 1, (1 << 16) - 1, None, (1 << 32) - 1]  # MAXVALS[n] is the maximum value of an unsigned n-byte number
SIGNS   = [None, 1 << 8 - 1, 1 << 16 - 1, None, 1 << 32 - 1]  # SIGNS[n] is the maximum absolute value of a signed n-byte number

####################
# JMP
####################
class JMP(Instruction):
    """
        Jump to a memory address.

        Operation:
            EIP = memory_location
    """

    def __init__(self):
        JNP = compile('not vm.reg.eflags_get(Reg32.PF)', 'jump', 'eval')
        JG = compile(
            'not vm.reg.eflags_get(Reg32.PF) and vm.reg.eflags_get(Reg32.SF) == vm.reg.eflags_get(Reg32.OF)',
            'jump', 'eval')
        JAE = compile('not vm.reg.eflags_get(Reg32.CF)', 'jump', 'eval')
        JGE = compile('vm.reg.eflags_get(Reg32.SF) == vm.reg.eflags_get(Reg32.OF)', 'jump', 'eval')
        JNO = compile('not vm.reg.eflags_get(Reg32.OF)', 'jump', 'eval')
        JNS = compile('not vm.reg.eflags_get(Reg32.SF)', 'jump', 'eval')
        JPE = compile('vm.reg.eflags_get(Reg32.PF)', 'jump', 'eval')
        JO = compile('vm.reg.eflags_get(Reg32.PF)', 'jump', 'eval')
        JL = compile('vm.reg.eflags_get(Reg32.SF) != vm.reg.eflags_get(Reg32.OF)', 'jump', 'eval')
        JCXZ = compile('not to_int(vm.reg.get(0, sz), byteorder)', 'jump', 'eval')
        JNBE = compile('not vm.reg.eflags_get(Reg32.CF) and not vm.reg.eflags_get(Reg32.ZF)', 'jump', 'eval')
        JNZ = compile('not vm.reg.eflags_get(Reg32.ZF)', 'jump', 'eval')
        JE = compile('vm.reg.eflags_get(Reg32.ZF)', 'jump', 'eval')
        JS = compile('vm.reg.eflags_get(Reg32.SF)', 'jump', 'eval')
        JBE = compile('vm.reg.eflags_get(Reg32.CF) or vm.reg.eflags_get(Reg32.ZF)', 'jump', 'eval')
        JLE = compile('vm.reg.eflags_get(Reg32.ZF) or vm.reg.eflags_get(Reg32.SF) != vm.reg.eflags_get(Reg32.OF)',
                      'jump', 'eval')
        JB = compile('vm.reg.eflags_get(Reg32.CF)', 'jump', 'eval')

        self.opcodes = {
            0xEB: P(self.rel, _8bit=True),
            0xE9: P(self.rel, _8bit=False),

            0xFF: self.rm_m,
            0xEA: P(self.ptr, _8bit=False),

            0x7B: P(self.rel, _8bit=True, jump=JNP),
            0x7F: P(self.rel, _8bit=True, jump=JG),
            0x73: P(self.rel, _8bit=True, jump=JAE),
            0x7D: P(self.rel, _8bit=True, jump=JGE),
            0x71: P(self.rel, _8bit=True, jump=JNO),
            0x79: P(self.rel, _8bit=True, jump=JNS),
            0x7A: P(self.rel, _8bit=True, jump=JPE),
            0x70: P(self.rel, _8bit=True, jump=JO),
            0x7C: P(self.rel, _8bit=True, jump=JL),
            0xE3: P(self.rel, _8bit=True, jump=JCXZ),
            0x77: P(self.rel, _8bit=True, jump=JNBE),
            0x75: P(self.rel, _8bit=True, jump=JNZ),
            0x74: P(self.rel, _8bit=True, jump=JE),
            0x78: P(self.rel, _8bit=True, jump=JS),
            0x76: P(self.rel, _8bit=True, jump=JBE),
            0x7E: P(self.rel, _8bit=True, jump=JLE),
            0x72: P(self.rel, _8bit=True, jump=JB),
            
            0x0F8C: P(self.rel, _8bit=False, jump=JL),
            0x0F84: P(self.rel, _8bit=False, jump=JE),
            0x0F82: P(self.rel, _8bit=False, jump=JB),
            0x0F85: P(self.rel, _8bit=False, jump=JNZ),
            0x0f8d: P(self.rel, _8bit=False, jump=JGE),
            0x0f86: P(self.rel, _8bit=False, jump=JBE),
            0x0f8e: P(self.rel, _8bit=False, jump=JLE),
            }

    def rel(vm, _8bit, jump=compile('True', 'jump', 'eval')) -> True:
        sz = 1 if _8bit else vm.operand_size

        d = vm.mem.get(vm.eip, sz)
        d = sign_extend(d, 4)
        d = to_int(d, True)
        vm.eip += sz

        if not eval(jump):
            return True
            
        tmpEIP = vm.eip + d
        if vm.operand_size == 2:
          tmpEIP &= MAXVALS[vm.operand_size]
          
        assert tmpEIP in vm.mem.bounds

        vm.eip = tmpEIP

        if debug: print('jmp rel{}({})'.format(sz * 8, hex(vm.eip)))
        
        return True

    def rm_m(vm) -> bool:
        old_eip = vm.eip

        sz = vm.operand_size
        RM, R = vm.process_ModRM(sz, sz)

        if R[1] == 4:  # this is jmp r/m
            disp = vm.mem.get(vm.eip, sz)
            vm.eip = to_int(disp) & MAXVALS[sz]

            assert vm.eip in vm.mem.bounds

            if debug: print('jmp rm{}({})'.format(sz * 8, vm.eip))

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

            vm.reg.CS = segment_selector

            if vm.operand_size == 4:
                vm.eip = tempEIP
            else:
                vm.eip = tempEIP & 0x0000FFFF

            if debug: print('jmp m{}({})'.format(sz * 8, vm.eip))

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

        vm.reg.CS = segment_selector

        if vm.operand_size == 4:
            vm.eip = tempEIP
        else:
            vm.eip = tempEIP & 0x0000FFFF

        if debug: print('jmp m{}({})'.format(sz * 8, vm.eip))

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
        imm = vm.mem.get(vm.eip, 1)  # always 8 bits
        imm = to_int(imm)
        vm.eip += 1

        vm.interrupt(imm)

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
    #rm_m = MagicMock(return_value=False)
    ptr = MagicMock(return_value=False)
    
    def rm_m(vm) -> bool:
        old_eip = vm.eip
        
        sz = vm.operand_size
        RM, R = vm.process_ModRM(sz, sz)
        
        if R[1] == 2:  # this is call r/m
          type, loc, size = RM

          data = (vm.mem if type else vm.reg).get(loc, size)
          
          tmpEIP = to_int(data) & MAXVALS[sz]
          
          # TODO: check whether tmpEIP is OK
          
          vm.stack_push(vm.eip.to_bytes(sz, byteorder))
          
          vm.eip = tmpEIP

          if debug: print(f'call {hex(loc) if type else reg_names[loc][sz]}={bytes(data)} => {hex(vm.eip)}')
          
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
        dest = to_int(dest, True)
        tmpEIP = vm.eip + dest

        assert tmpEIP in vm.mem.bounds

        vm.stack_push(vm.eip.to_bytes(sz, byteorder, signed=True))
        vm.eip = tmpEIP

        if debug: print(f'call {hex(dest)} => {hex(vm.eip)}')

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
        vm.eip = to_int(vm.stack_pop(sz), True)

        assert vm.eip in vm.mem.bounds

        if debug: print("ret (eip=0x{:02x})".format(vm.eip))

        return True

    def near_imm(vm) -> True:
        sz = 2  # always 16 bits
        vm.eip = to_int(vm.stack_pop(sz), True)

        imm = to_int(vm.mem.get(vm.eip, sz))
        vm.eip += sz

        vm.stack_pop(imm)

        assert vm.eip in vm.mem.bounds

        if debug: print("ret (eip=0x{:02x})".format(vm.eip))

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

        self.reg.set(ESP, self.reg.get(EBP, self.address_size))
        self.reg.set(EBP, self.stack_pop(self.operand_size))

        return True
