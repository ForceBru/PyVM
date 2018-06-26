from ..debug import debug
from ..Registers import Reg32
from ..util import Instruction, to_int, byteorder
from ..misc import sign_extend, zero_extend

from functools import partialmethod as P
from unittest.mock import MagicMock

MAXVALS = [None, (1 << 8) - 1, (1 << 16) - 1, None, (1 << 32) - 1]  # MAXVALS[n] is the maximum value of an unsigned n-bit number
SIGNS   = [None, 1 << 8 - 1, 1 << 16 - 1, None, 1 << 32 - 1]  # SIGNS[n] is the maximum absolute value of a signed n-bit number

####################
# MOV
####################
class MOV(Instruction):
    """
    Move data from one location (a) to another (b).

    Flags:
        None affected

    Operation: b <- a
    """

    def __init__(self):
        self.opcodes = {
            **{
                o: P(self.r_imm, _8bit=True)
                for o in range(0xB0, 0xB8)
                },
            **{
                o: P(self.r_imm, _8bit=False)
                for o in range(0xB8, 0xC0)
                },
            0xC6: P(self.rm_imm, _8bit=True),
            0xC7: P(self.rm_imm, _8bit=False),

            0x88: P(self.rm_r, _8bit=True, reverse=False),
            0x89: P(self.rm_r, _8bit=False, reverse=False),

            0x8A: P(self.rm_r, _8bit=True, reverse=True),
            0x8B: P(self.rm_r, _8bit=False, reverse=True),

            0x8C: P(self.rm_sreg, reverse=False),
            0x8E: P(self.rm_sreg, reverse=True),

            0xA0: P(self.r_moffs, reverse=False, _8bit=True),
            0xA1: P(self.r_moffs, reverse=False, _8bit=False),

            0xA2: P(self.r_moffs, reverse=True, _8bit=True),
            0xA3: P(self.r_moffs, reverse=True, _8bit=False),
            }

    # TODO: implement MOV with sreg
    rm_sreg = MagicMock(return_value=False)

    def r_imm(vm, _8bit) -> True:
        sz = 1 if _8bit else vm.operand_size

        imm = vm.mem.get(vm.eip, sz)
        vm.eip += sz

        r = vm.opcode & 0b111
        vm.reg.set(r, imm)

        if debug:
            print('mov r{0}({1}),imm{0}({2})'.format(sz * 8, r, imm))

        return True

    def rm_imm(vm, _8bit) -> bool:
        sz = 1 if _8bit else vm.operand_size
        old_eip = vm.eip

        RM, R = vm.process_ModRM(sz, sz)

        if R[1] != 0:
            vm.eip = old_eip
            return False  # this is not MOV

        type, loc, _ = RM

        imm = vm.mem.get(vm.eip, sz)
        vm.eip += sz

        (vm.mem if type else vm.reg).set(loc, imm)

        if debug:
            print('mov {0}{1}({2}),imm{1}({3})'.format(('m' if type else '_r'), sz * 8, loc, imm))

        return True

    def rm_r(vm, _8bit, reverse=False, movsx=False) -> True:
        sz = 1 if _8bit else vm.operand_size

        RM, R = vm.process_ModRM(sz, sz)

        type, loc, _ = RM

        if reverse:
            data = (vm.mem if type else vm.reg).get(loc, sz)
            
            vm.reg.set(R[1], data)

            if debug: print('mov r{1}({2}),{0}{1}({3})'.format(('m' if type else '_r'), sz * 8, R[1], data))
        else:
            data = vm.reg.get(R[1], R[2])
            (vm.mem if type else vm.reg).set(loc, data)

            if debug: print('mov {0}{1}({2}),r{1}({3})'.format(('m' if type else '_r'), sz * 8, loc, data))

        return True

    def r_moffs(vm, _8bit, reverse=False) -> True:
        sz = 1 if _8bit else vm.operand_size

        loc = to_int(vm.mem.get(vm.eip, vm.address_size))
        vm.eip += vm.address_size

        if reverse:
            data = vm.reg.get(0, sz)
            vm.mem.set(loc, data)
        else:
            data = vm.mem.get(loc, sz)
            vm.reg.set(0, data)

        msg = 'mov moffs{1}({2}), {0}({3})' if reverse else 'mov {0}, moffs{1}({2}:{3})'

        if debug: print(msg.format({1: 'al', 2: 'ax', 4: 'eax'}[sz], sz * 8, loc, data))

        return True


####################
# MOVSX / MOVSXD / MOVZX
####################
class MOVSX(Instruction):
  """
  Move and sign extend
  """
  
  def __init__(self):
    self.opcodes = {
      0x0FBE: P(self.r_rm, _8bit=True),
      0x0FBF: P(self.r_rm, _8bit=False),
      
      0x63: P(self.r_rm, _8bit=False, movsxd=True),
      
      0x0FB6: P(self.r_rm, _8bit=True, movzx=True),
      0x0FB7: P(self.r_rm, _8bit=False, movzx=True),
    }
  
  def r_rm(vm, _8bit, movsxd=False, movzx=False) -> True:
    sz = 1 if _8bit else vm.operand_size
    
    if movsxd:
      RM, R = vm.process_ModRM(sz, sz)
    else:
      RM, R = vm.process_ModRM(sz, vm.operand_size) # different sizes!

    type, From, size = RM
    
    SRC = (vm.mem if type else vm.reg).get(From, size)
    
    if movzx:
      SRC = zero_extend(SRC, R[2])
    else:
      SRC = sign_extend(SRC, R[2])
    
    vm.reg.set(R[1], SRC)
    
    if debug: print(f'movsx{"d" if movsxd else ""} r{sz} {"m" if type else "r"}{size}')
    
    return True
    
    

####################
# PUSH
####################
class PUSH(Instruction):
    """
    Push data onto the stack.
    """

    def __init__(self):
        self.opcodes = {
            **{
                o: self.r
                for o in range(0x50, 0x58)
                },
            0xFF  : self.rm,

            0x6A  : P(self.imm, _8bit=True),
            0x68  : P(self.imm, _8bit=False),

            0x0E  : P(self.sreg, 'CS'),
            0x16  : P(self.sreg, 'SS'),
            0x1E  : P(self.sreg, 'DS'),
            0x06  : P(self.sreg, 'ES'),

            0x0FA0: P(self.sreg, 'FS'),
            0x0FA8: P(self.sreg, 'GS')
            }

    def r(vm) -> True:
        sz = vm.operand_size

        loc = vm.opcode & 0b111
        data = vm.reg.get(loc, sz)
        if debug: print('push r{}({})'.format(sz * 8, loc))
        vm.stack_push(data)

        return True

    def rm(vm) -> bool:
        old_eip = vm.eip
        sz = vm.operand_size

        RM, R = vm.process_ModRM(sz, sz)

        if R[1] != 6:
            vm.eip = old_eip
            return False  # this is not PUSH rm

        type, loc, _ = RM

        data = (vm.mem if type else vm.reg).get(loc, sz)
        vm.stack_push(data)

        if debug: print('push {2}{0}({1})'.format(sz * 8, data, ('m' if type else '_r')))
        return True

    def imm(vm, _8bit=False) -> True:
        sz = 1 if _8bit else vm.operand_size

        data = vm.mem.get(vm.eip, sz)
        vm.eip += sz

        vm.stack_push(data)

        if debug: print('push imm{}({})'.format(sz * 8, data))

        return True

    def sreg(vm, reg: str) -> True:
        """
        Push a segment register onto the stack.

        :param reg: the name of the register to be pushed.
        """

        vm.stack_push(getattr(vm.reg, reg).to_bytes(2, byteorder))
        if debug: print('push {}'.format(reg))

        return True


####################
# POP
####################
class POP(Instruction):
    """
    Pop data from the stack.
    """

    def __init__(self):
        self.opcodes = {
            **{
                o: self.r
                for o in range(0x58, 0x60)
                },
            0x8F  : self.rm,

            0x1F  : P(self.sreg, 'DS'),
            0x07  : P(self.sreg, 'ES'),
            0x17  : P(self.sreg, 'SS'),

            0x0FA1: P(self.sreg, 'FS', _32bit=True),
            0x0FA9: P(self.sreg, 'GS', _32bit=True)
            }

    def r(vm) -> True:
        sz = vm.operand_size

        loc = vm.opcode & 0b111
        data = vm.stack_pop(sz)
        vm.reg.set(loc, data)
        if debug: print('pop r{}({})'.format(sz * 8, loc))

        return True

    def rm(vm) -> bool:
        sz = vm.operand_size
        old_eip = vm.eip

        RM, R = vm.process_ModRM(sz, sz)

        if R[1] != 0:
            vm.eip = old_eip
            return False  # this is not POP rm

        type, loc, _ = RM

        data = vm.stack_pop(sz)

        (vm.mem if type else vm.reg).set(loc, data)

        if debug: print('pop {2}{0}({1})'.format(sz * 8, data, ('m' if type else '_r')))

        return True

    def sreg(vm, reg: str, _32bit=False) -> True:
        sz = 4 if _32bit else 2

        data = vm.stack_pop(sz)

        setattr(vm.reg, reg, to_int(data, False))
        if debug: print('pop {}'.format(reg))

        return True


####################
# LEA
####################
class LEA(Instruction):
    def __init__(self):
        self.opcodes = {
            0x8D: self.r_rm
            }

    def r_rm(self) -> True:
        RM, R = self.process_ModRM(self.operand_size, self.operand_size)

        type, loc, sz = RM

        if (self.operand_size == 2) and (self.address_size == 2):
            tmp = loc
        elif (self.operand_size == 2) and (self.address_size == 4):
            tmp = loc & 0xffff
        elif (self.operand_size == 4) and (self.address_size == 2):
            tmp = loc
        elif (self.operand_size == 4) and (self.address_size == 4):
            tmp = loc
        else:
            raise RuntimeError("Invalid operand size / address size")

        self.reg.set(R[1], tmp.to_bytes(self.operand_size, byteorder))
        
        if debug: print('lea r{0}({1}),{3}{0}({2})'.format(sz * 8, R[1], loc, ('m' if type else '_r')))

        return True

####################
# XCHG
####################
class XCHG(Instruction):
    def __init__(self):
        self.opcodes = {
            **{
                o: self.eax_r
                for o in range(0x90, 0x98)
                },
            0x86: P(self.rm_r, _8bit=True),
            0x87: P(self.rm_r, _8bit=False)
            }

    def eax_r(vm) -> True:
        sz = vm.operand_size
        loc = vm.opcode & 0b111

        if loc != 0:  # not EAX
            tmp = vm.reg.get(0, sz)
            vm.reg.set(0, vm.reg.get(loc, sz))
            vm.reg.set(loc, tmp)

        if debug: print('xchg eax, r{}({})'.format(sz * 8, loc))
        return True

    def rm_r(vm, _8bit) -> True:
        sz = 1 if _8bit else vm.operand_size

        RM, R = vm.process_ModRM(sz, sz)
        type, loc, _ = RM

        if loc != R[1]:
            tmp = (vm.mem if type else vm.reg).get(loc, sz)
            (vm.mem if type else vm.reg).set(loc, vm.reg.get(R[1], sz))
            vm.reg.set(R[1], tmp)

        if debug: print('xchg r{1}({2}),{0}{1}({3})'.format(('m' if type else '_r'), sz * 8, R[1], tmp))
        return True

####################
# CBW / CWDE
####################
class CBW(Instruction):
    def __init__(self):
        self.opcodes = {
            0x98: self.cbwcwde
            }

    def cbwcwde(self) -> True:
        self.reg.set(0, sign_extend(self.reg.get(0, self.operand_size // 2), self.operand_size))

        if debug: print('cbw' if self.operand_size == 2 else 'cwde')
        return True


####################
# CMC
####################
class CMC(Instruction):
    def __init__(self):
        self.opcodes = {
            0xF5: self.cmc
            }

    def cmc(self) -> True:
        self.reg.eflags_set(Reg32.CF, not self.reg.eflags_get(Reg32.CF))

        if debug: print('cmc')
        return True

####################
# MOVS
####################
class MOVS(Instruction):
    def __init__(self):
        self.opcodes = {
            0xA4: P(self.movs, _8bit=True),
            0xA5: P(self.movs, _8bit=False)
            }

    def movs(self, _8bit) -> True:
        sz = 1 if _8bit else self.operand_size

        esi = to_int(self.reg.get(6, sz))
        edi = to_int(self.reg.get(7, sz))

        self.mem.set(esi, self.mem.get(edi, sz))

        if not self.reg.eflags_get(Reg32.DF):
            esi += sz
            edi += sz
        else:
            esi -= sz
            edi -= sz

        esi &= MAXVALS[sz]
        edi &= MAXVALS[sz]

        self.reg.set(6, esi, self.to_bytes(sz, byteorder))
        self.reg.set(7, edi, self.to_bytes(sz, byteorder))

        if debug: print('mov{}'.format('s' if sz == 1 else ('w' if sz == 2 else 'd')))
        return True

####################
# CWD / CDQ
####################
class CWD(Instruction):
    def __init__(self):
        self.opcodes = {
            0x99: self.cwd_cdq
            }

    def cwd_cdq(self) -> True:
        sz = self.operand_size

        tmp = sign_extend(self.reg.get(0, sz), sz * 2)  # AX / EAX

        self.reg.set(2, tmp[sz:])  # DX/EDX
        self.reg.set(0, tmp[:sz])  # AX/EAX

        if debug: print('cwd' if sz == 2 else 'cdq')
        return True

####################
# CLC / CLD / STC / STD
####################
class CLC(Instruction):
    def __init__(self):
        self.opcodes = {
            0xF8: P(self.set_stuff, Reg32.CF, 0),
            0xFC: P(self.set_stuff, Reg32.DF, 0),
            0xF9: P(self.set_stuff, Reg32.CF, 1),
            0xFD: P(self.set_stuff, Reg32.DF, 1)
            }

    def set_stuff(self, flag, val):
        self.reg.eflags_set(flag, val)
