import sys
import operator
from functools import partial as P

from .CPU import CPU32, to_int, byteorder
from .debug import debug
from .Registers import Reg32
from .misc import Shift

__all__ = ['VM']


class VM(CPU32):
    """
    This is a 'big' class (term coined by @ForceBru), that is, its member functions are distributed across multiple files
    to avoid code bloat and then imported right inside the class definition, so that upon class initialization
    they act as regular member functions. Thus, for any of these functions, it's essential to accept the `self` argument.

    Purpose of the main modules:
        1) `fetchLoop` - provides code execution routines
        2) `internals` - provides implementations of various instructions in the form of functions to avoid code duplication
        3) `kernel`    - implements some basic routines, usually provided by the Linux kernel
        4) `misc`      - miscellaneous parsing routines

    The actual instructions are to be implemented in `instructions.py`. To add the instruction to the VM, add a dictionary
    in the following format to `VM.__init__`:

        self._mnemonic = {
            opcode1: P(self.OPCODE_IMPL.argtype1, arg1=value1, arg2=value2, ...),
            opcode2: P(self.OPCODE_IMPL.argtype1, arg1=value3, arg2=value4, ...),

            opcode3: P(self.OPCODE_IMPL.argtype2, arg3=value5, arg4=value6, ...),
            ...
        }

    This should be done in such a way that all the arguments to the instruction implementation are provided in this dictionary
    and the call `self._mnemonic[valid_opcode]()` would work.
    """

    from .fetchLoop import execute_opcode, run, execute_bytes, execute_file, override
    from .misc import process_ModRM
    
    from .instructions import \
        MOV, movs, XCHG, lea, \
        JMP, CALL, RET, leave, \
        INT, \
        PUSH, POP, \
        ADDSUB, INCDEC, mul, IMUL, div, \
        BITWISE, NEGNOT, shift, \
        cbwcwde, cmc, cwd_cdq

    from .kernel import sys_exit, sys_read, sys_write

    def __init__(self, memsize: int, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
        super().__init__(memsize)

        self.modes = (32, 16)  # number of bits
        self.sizes = (4, 2)  # number of bytes
        self.default_mode = 0  # 0 == 32-bit mode; 1 == 16-bit mode
        self.current_mode = self.default_mode
        self.operand_size = self.sizes[self.current_mode]
        self.address_size = self.sizes[self.current_mode]

        self.fmt = '\t[0x{:0' + str(len(str(self.mem.size))//16) + 'x}]: 0x{:02x}'

        self.descriptors = [stdin, stdout, stderr]
        self.running = True

        self._mov = {
            **{
                o: P(self.MOV.r_imm, self, _8bit=True)
                for o in range(0xB0, 0xB8)
                },
            **{
                o: P(self.MOV.r_imm, self, _8bit=False)
                for o in range(0xB8, 0xC0)
                },
            0xC6: P(self.MOV.rm_imm, self, _8bit=True),
            0xC7: P(self.MOV.rm_imm, self, _8bit=False),

            0x88: P(self.MOV.rm_r, self, _8bit=True,  reverse=False),
            0x89: P(self.MOV.rm_r, self, _8bit=False, reverse=False),

            0x8A: P(self.MOV.rm_r, self, _8bit=True,  reverse=True),
            0x8B: P(self.MOV.rm_r, self, _8bit=False, reverse=True),

            0x8C: P(self.MOV.rm_sreg, self, reverse=False),
            0x8E: P(self.MOV.rm_sreg, self, reverse=True),

            0xA0: P(self.MOV.r_moffs, self, reverse=False, _8bit=True),
            0xA1: P(self.MOV.r_moffs, self, reverse=False, _8bit=False),

            0xA2: P(self.MOV.r_moffs, self, reverse=True, _8bit=True),
            0xA3: P(self.MOV.r_moffs, self, reverse=True, _8bit=False),
            }

        self._jmp = {
            0xEB: P(self.JMP.rel, self, _8bit=True),
            0xE9: P(self.JMP.rel, self, _8bit=False),

            0xFF: P(self.JMP.rm_m, self, _8bit=False),
            0xEA: P(self.JMP.ptr, self, _8bit=False),
            }

        self._int = {
            0xCC: P(self.INT._3, self),
            0xCD: P(self.INT.imm, self)
            }

        self._push = {
            **{
                o: P(self.PUSH.r, self)
                for o in range(0x50, 0x58)
                },
            0xFF: P(self.PUSH.rm, self),

            0x6A: P(self.PUSH.imm, self, _8bit=True),
            0x68: P(self.PUSH.imm, self, _8bit=False),

            0x0E: P(self.PUSH.sreg, self, 'CS'),
            0x16: P(self.PUSH.sreg, self, 'SS'),
            0x1E: P(self.PUSH.sreg, self, 'DS'),
            0x06: P(self.PUSH.sreg, self, 'ES'),

            0x0FA0: P(self.PUSH.sreg, self, 'FS'),
            0x0FA8: P(self.PUSH.sreg, self, 'GS')
            }

        self._pop = {
            **{
                o: P(self.POP.r, self)
                for o in range(0x58, 0x60)
                },
            0x8F: P(self.POP.rm, self),

            0x1F: P(self.POP.sreg, self, 'DS'),
            0x07: P(self.POP.sreg, self, 'ES'),
            0x17: P(self.POP.sreg, self, 'SS'),

            0x0FA1: P(self.POP.sreg, self, 'FS', _32bit=True),
            0x0FA9: P(self.POP.sreg, self, 'GS', _32bit=True)
            }

        self._call = {
            0xE8: P(self.CALL.rel, self),
            0xFF: P(self.CALL.rm_m, self),
            0x9A: P(self.CALL.ptr, self)
            }

        self._ret = {
            0xC3: P(self.RET.near, self),
            0xCB: P(self.RET.far, self),

            0xC2: P(self.RET.near_imm, self),
            0xCA: P(self.RET.far_imm, self)
            }

        self._add = {
            0x04: P(self.ADDSUB.r_imm, self, _8bit=True),
            0x05: P(self.ADDSUB.r_imm, self, _8bit=False),

            0x80: P(self.ADDSUB.rm_imm, self, _8bit_op=True, _8bit_imm=True),
            0x81: P(self.ADDSUB.rm_imm, self, _8bit_op=False, _8bit_imm=False),
            0x83: P(self.ADDSUB.rm_imm, self, _8bit_op=False, _8bit_imm=True),

            0x00: P(self.ADDSUB.rm_r, self, _8bit=True),
            0x01: P(self.ADDSUB.rm_r, self, _8bit=False),
            0x02: P(self.ADDSUB.r_rm, self, _8bit=True),
            0x03: P(self.ADDSUB.r_rm, self, _8bit=False),
            }

        self._sub = {
            0x2C: P(self.ADDSUB.r_imm, self, _8bit=True, sub=True),
            0x2D: P(self.ADDSUB.r_imm, self, _8bit=False, sub=True),

            0x80: P(self.ADDSUB.rm_imm, self, _8bit_op=True, _8bit_imm=True, sub=True),
            0x81: P(self.ADDSUB.rm_imm, self, _8bit_op=False, _8bit_imm=False, sub=True),
            0x83: P(self.ADDSUB.rm_imm, self, _8bit_op=False, _8bit_imm=True, sub=True),

            0x28: P(self.ADDSUB.rm_r, self, _8bit=True, sub=True),
            0x29: P(self.ADDSUB.rm_r, self, _8bit=False, sub=True),
            0x2A: P(self.ADDSUB.r_rm, self, _8bit=True, sub=True),
            0x2B: P(self.ADDSUB.r_rm, self, _8bit=False, sub=True),
            }

        self._lea = {
            0x8D: P(self.lea)
            }

        self._cmp = {
            0x3C: P(self.ADDSUB.r_imm, self, _8bit=True,  sub=True, cmp=True),
            0x3D: P(self.ADDSUB.r_imm, self, _8bit=False, sub=True, cmp=True),

            0x80: P(self.ADDSUB.rm_imm, self, _8bit_op=True,  _8bit_imm=True,  sub=True, cmp=True),
            0x81: P(self.ADDSUB.rm_imm, self, _8bit_op=False, _8bit_imm=False, sub=True, cmp=True),
            0x83: P(self.ADDSUB.rm_imm, self, _8bit_op=False, _8bit_imm=True,  sub=True, cmp=True),

            0x38: P(self.ADDSUB.rm_r, self, _8bit=True,  sub=True, cmp=True),
            0x39: P(self.ADDSUB.rm_r, self, _8bit=False, sub=True, cmp=True),
            0x3A: P(self.ADDSUB.r_rm, self, _8bit=True,  sub=True, cmp=True),
            0x3B: P(self.ADDSUB.r_rm, self, _8bit=False, sub=True, cmp=True),
            }

        JNP  = compile('not vm.reg.eflags_get(Reg32.PF)', 'jump', 'eval')
        JG   = compile(
                'not vm.reg.eflags_get(Reg32.PF) and vm.reg.eflags_get(Reg32.SF) == vm.reg.eflags_get(Reg32.OF)',
                'jump', 'eval')
        JAE  = compile('not vm.reg.eflags_get(Reg32.CF)', 'jump', 'eval')
        JGE  = compile('vm.reg.eflags_get(Reg32.SF) == vm.reg.eflags_get(Reg32.OF)', 'jump', 'eval')
        JNO  = compile('not vm.reg.eflags_get(Reg32.OF)', 'jump', 'eval')
        JNS  = compile('not vm.reg.eflags_get(Reg32.SF)', 'jump', 'eval')
        JPE  = compile('vm.reg.eflags_get(Reg32.PF)', 'jump', 'eval')
        JO   = compile('vm.reg.eflags_get(Reg32.PF)', 'jump', 'eval')
        JL   = compile('vm.reg.eflags_get(Reg32.SF) != vm.reg.eflags_get(Reg32.OF)', 'jump', 'eval')
        JCXZ = compile('not to_int(vm.reg.get(0, sz), byteorder)', 'jump', 'eval')
        JNBE = compile('not vm.reg.eflags_get(Reg32.CF) and not vm.reg.eflags_get(Reg32.ZF)', 'jump', 'eval')
        JNZ  = compile('not vm.reg.eflags_get(Reg32.ZF)', 'jump', 'eval')
        JE   = compile('vm.reg.eflags_get(Reg32.ZF)', 'jump', 'eval')
        JS   = compile('vm.reg.eflags_get(Reg32.SF)', 'jump', 'eval')
        JBE  = compile('vm.reg.eflags_get(Reg32.CF) or vm.reg.eflags_get(Reg32.ZF)', 'jump', 'eval')
        JLE  = compile('vm.reg.eflags_get(Reg32.ZF) or vm.reg.eflags_get(Reg32.SF) != vm.reg.eflags_get(Reg32.OF)', 'jump', 'eval')
        JB   = compile('vm.reg.eflags_get(Reg32.CF)', 'jump', 'eval')
        self._jcc = {
            0x7B: P(self.JMP.rel, self, _8bit=True, jump=JNP),
            0x7F: P(self.JMP.rel, self, _8bit=True, jump=JG),
            0x73: P(self.JMP.rel, self, _8bit=True, jump=JAE),
            0x7D: P(self.JMP.rel, self, _8bit=True, jump=JGE),
            0x71: P(self.JMP.rel, self, _8bit=True, jump=JNO),
            0x79: P(self.JMP.rel, self, _8bit=True, jump=JNS),
            0x7A: P(self.JMP.rel, self, _8bit=True, jump=JPE),
            0x70: P(self.JMP.rel, self, _8bit=True, jump=JO),
            0x7C: P(self.JMP.rel, self, _8bit=True, jump=JL),
            0xE3: P(self.JMP.rel, self, _8bit=True, jump=JCXZ),
            0x77: P(self.JMP.rel, self, _8bit=True, jump=JNBE),
            0x75: P(self.JMP.rel, self, _8bit=True, jump=JNZ),
            0x74: P(self.JMP.rel, self, _8bit=True, jump=JE),
            0x78: P(self.JMP.rel, self, _8bit=True, jump=JS),
            0x76: P(self.JMP.rel, self, _8bit=True, jump=JBE),
            0x7E: P(self.JMP.rel, self, _8bit=True, jump=JLE),
            0x72: P(self.JMP.rel, self, _8bit=True, jump=JB)
            }

        self._and = {
            0x24: P(self.BITWISE.r_imm, self, _8bit=True, operation=operator.and_),
            0x25: P(self.BITWISE.r_imm, self, _8bit=False, operation=operator.and_),

            0x80: P(self.BITWISE.rm_imm, self, _8bit=True, _8bit_imm=True, operation=operator.and_),
            0x81: P(self.BITWISE.rm_imm, self, _8bit=False, _8bit_imm=False, operation=operator.and_),
            0x83: P(self.BITWISE.rm_imm, self, _8bit=False, _8bit_imm=True, operation=operator.and_),

            0x20: P(self.BITWISE.rm_r, self, _8bit=True, operation=operator.and_),
            0x21: P(self.BITWISE.rm_r, self, _8bit=False, operation=operator.and_),

            0x22: P(self.BITWISE.r_rm, self, _8bit=True, operation=operator.and_),
            0x23: P(self.BITWISE.r_rm, self, _8bit=False, operation=operator.and_),
            }

        self._or = {
            0x0C: P(self.BITWISE.r_imm, self, _8bit=True, operation=operator.or_),
            0x0D: P(self.BITWISE.r_imm, self, _8bit=False, operation=operator.or_),

            0x80: P(self.BITWISE.rm_imm, self, _8bit=True, _8bit_imm=True, operation=operator.or_),
            0x81: P(self.BITWISE.rm_imm, self, _8bit=False, _8bit_imm=False, operation=operator.or_),
            0x83: P(self.BITWISE.rm_imm, self, _8bit=False, _8bit_imm=True, operation=operator.or_),

            0x08: P(self.BITWISE.rm_r, self, _8bit=True, operation=operator.or_),
            0x09: P(self.BITWISE.rm_r, self, _8bit=False, operation=operator.or_),

            0x0A: P(self.BITWISE.r_rm, self, _8bit=True, operation=operator.or_),
            0x0B: P(self.BITWISE.r_rm, self, _8bit=False, operation=operator.or_),
            }

        self._xor = {
            0x34: P(self.BITWISE.r_imm, self, _8bit=True, operation=operator.xor),
            0x35: P(self.BITWISE.r_imm, self, _8bit=False, operation=operator.xor),

            0x80: P(self.BITWISE.rm_imm, self, _8bit=True, _8bit_imm=True, operation=operator.xor),
            0x81: P(self.BITWISE.rm_imm, self, _8bit=False, _8bit_imm=False, operation=operator.xor),
            0x83: P(self.BITWISE.rm_imm, self, _8bit=False, _8bit_imm=True, operation=operator.xor),

            0x30: P(self.BITWISE.rm_r, self, _8bit=True, operation=operator.xor),
            0x31: P(self.BITWISE.rm_r, self, _8bit=False, operation=operator.xor),

            0x32: P(self.BITWISE.r_rm, self, _8bit=True, operation=operator.xor),
            0x33: P(self.BITWISE.r_rm, self, _8bit=False, operation=operator.xor),
            }

        self._neg = {
            0xF6: P(self.NEGNOT.rm, self, _8bit=True, operation=0),
            0xF7: P(self.NEGNOT.rm, self, _8bit=False, operation=0)
            }

        self._not = {
            0xF6: P(self.NEGNOT.rm, self, _8bit=True, operation=1),
            0xF7: P(self.NEGNOT.rm, self, _8bit=False, operation=1)
            }

        self._test = {
            0xA8: P(self.BITWISE.r_imm, self, _8bit=True, operation=operator.and_, test=True),
            0xA9: P(self.BITWISE.r_imm, self, _8bit=False, operation=operator.and_, test=True),

            0xF6: P(self.BITWISE.rm_imm, self, _8bit=True, _8bit_imm=True, operation=operator.and_, test=True),
            0xF7: P(self.BITWISE.rm_imm, self, _8bit=False, _8bit_imm=False, operation=operator.and_, test=True),

            0x84: P(self.BITWISE.rm_r, self, _8bit=True, operation=operator.and_, test=True),
            0x85: P(self.BITWISE.rm_r, self, _8bit=False, operation=operator.and_, test=True),
            }

        self._inc = {
            **{
                o: P(self.INCDEC.r, self, _8bit=False)
                for o in range(0x40, 0x48)
                },
            0xFE: P(self.INCDEC.rm, self, _8bit=True),
            0xFF: P(self.INCDEC.rm, self, _8bit=False),
            }

        self._dec = {
            **{
                o: P(self.INCDEC.r, self, _8bit=False, dec=True)
                for o in range(0x48, 0x50)
                },
            0xFE: P(self.INCDEC.rm, self, _8bit=True, dec=True),
            0xFF: P(self.INCDEC.rm, self, _8bit=False, dec=True),
            }

        self._adc = {
            0x14: P(self.ADDSUB.r_imm, self, _8bit=True, carry=True),
            0x15: P(self.ADDSUB.r_imm, self, _8bit=False, carry=True),

            0x80: P(self.ADDSUB.rm_imm, self, _8bit_op=True, _8bit_imm=True, carry=True),
            0x81: P(self.ADDSUB.rm_imm, self, _8bit_op=False, _8bit_imm=False, carry=True),
            0x83: P(self.ADDSUB.rm_imm, self, _8bit_op=False, _8bit_imm=True, carry=True),

            0x10: P(self.ADDSUB.rm_r, self, _8bit=True, carry=True),
            0x11: P(self.ADDSUB.rm_r, self, _8bit=False, carry=True),
            0x12: P(self.ADDSUB.r_rm, self, _8bit=True, carry=True),
            0x13: P(self.ADDSUB.r_rm, self, _8bit=False, carry=True),
            }

        self._sbb = {
            0x1C: P(self.ADDSUB.r_imm, self, _8bit=True, sub=True, carry=True),
            0x1D: P(self.ADDSUB.r_imm, self, _8bit=False, sub=True, carry=True),

            0x80: P(self.ADDSUB.rm_imm, self, _8bit_op=True, _8bit_imm=True, sub=True, carry=True),
            0x81: P(self.ADDSUB.rm_imm, self, _8bit_op=False, _8bit_imm=False, sub=True, carry=True),
            0x83: P(self.ADDSUB.rm_imm, self, _8bit_op=False, _8bit_imm=True, sub=True, carry=True),

            0x18: P(self.ADDSUB.rm_r, self, _8bit=True, sub=True, carry=True),
            0x19: P(self.ADDSUB.rm_r, self, _8bit=False, sub=True, carry=True),
            0x1A: P(self.ADDSUB.r_rm, self, _8bit=True, sub=True, carry=True),
            0x1B: P(self.ADDSUB.r_rm, self, _8bit=False, sub=True, carry=True),
            }

        self._leave = {
            0xC9: P(self.leave)
            }

        self._shl = {
            0xD0: P(self.shift, operation=Shift.SHL, cnt=Shift.C_ONE, _8bit=True),
            0xD2: P(self.shift, operation=Shift.SHL, cnt=Shift.C_CL, _8bit=True),
            0xC0: P(self.shift, operation=Shift.SHL, cnt=Shift.C_imm8, _8bit=True),

            0xD1: P(self.shift, operation=Shift.SHL, cnt=Shift.C_ONE, _8bit=False),
            0xD3: P(self.shift, operation=Shift.SHL, cnt=Shift.C_CL, _8bit=False),
            0xC1: P(self.shift, operation=Shift.SHL, cnt=Shift.C_imm8, _8bit=False)
            }

        self._shr = {
            0xD0: P(self.shift, operation=Shift.SHR, cnt=Shift.C_ONE, _8bit=True),
            0xD2: P(self.shift, operation=Shift.SHR, cnt=Shift.C_CL, _8bit=True),
            0xC0: P(self.shift, operation=Shift.SHR, cnt=Shift.C_imm8, _8bit=True),

            0xD1: P(self.shift, operation=Shift.SHR, cnt=Shift.C_ONE, _8bit=False),
            0xD3: P(self.shift, operation=Shift.SHR, cnt=Shift.C_CL, _8bit=False),
            0xC1: P(self.shift, operation=Shift.SHR, cnt=Shift.C_imm8, _8bit=False)
            }

        self._sar = {
            0xD0: P(self.shift, operation=Shift.SAR, cnt=Shift.C_ONE, _8bit=True),
            0xD2: P(self.shift, operation=Shift.SAR, cnt=Shift.C_CL, _8bit=True),
            0xC0: P(self.shift, operation=Shift.SAR, cnt=Shift.C_imm8, _8bit=True),

            0xD1: P(self.shift, operation=Shift.SAR, cnt=Shift.C_ONE, _8bit=False),
            0xD3: P(self.shift, operation=Shift.SAR, cnt=Shift.C_CL, _8bit=False),
            0xC1: P(self.shift, operation=Shift.SAR, cnt=Shift.C_imm8, _8bit=False)
            }

        self._clc = {
            0xF8: P(self.reg.eflags_set, Reg32.CF, 0)
            }

        self._cld = {
            0xFC: P(self.reg.eflags_set, Reg32.DF, 0)
            }

        self._stc = {
            0xF9: P(self.reg.eflags_set, Reg32.CF, 1)
            }

        self._std = {
            0xFD: P(self.reg.eflags_set, Reg32.DF, 1)
            }

        self._xchg = {
            **{
                o: P(self.XCHG.eax_r, self)
                for o in range(0x90, 0x98)
                },
            0x86: P(self.XCHG.rm_r, self, _8bit=True),
            0x87: P(self.XCHG.rm_r, self, _8bit=False)
            }

        self._cbw = {
            0x98: P(self.cbwcwde)
            }

        self._cmc = {
            0x98: P(self.cmc)
            }

        self._movs = {
            0xA4: P(self.movs, _8bit=True),
            0xA5: P(self.movs, _8bit=False)
            }

        self._mul = {
            0xF6: P(self.mul, _8bit=True),
            0xF7: P(self.mul, _8bit=False)
            }

        self._div = {
            0xF6: P(self.div, _8bit=True),
            0xF7: P(self.div, _8bit=False)
            }

        self._imul = {
            0xF6: P(self.IMUL.rm, self, _8bit=True),
            0xF7: P(self.IMUL.rm, self, _8bit=False),

            0x0FAF: P(self.IMUL.r_rm, self),

            0x6B: P(self.IMUL.r_rm_imm, self, _8bit_imm=True),
            0x69: P(self.IMUL.r_rm_imm, self, _8bit_imm=True)
            }

        self._idiv = {
            0xF6: P(self.div, _8bit=True, idiv=True),
            0xF7: P(self.div, _8bit=False, idiv=True)
            }

        self._cwd = {
            0x99: P(self.cwd_cdq)
            }

        self.instr = {}
        
        for instruction in (getattr(self, name) for name in dir(self) if name.startswith('_') and not name.startswith('__')):
            for opcode, impl in instruction.items():
                self.instr.setdefault(opcode, set())
                self.instr[opcode].add(impl)

    def interrupt(self, code: int):
        valid_codes = [0x80]

        if code == valid_codes[0]:  # syscall
            valid_syscalls = {
                0x1: self.sys_exit,
                0x3: self.sys_read,
                0x4: self.sys_write
                }

            syscall = to_int(self.reg.get(0, 4))  # EAX

            try:
                valid_syscalls[syscall]()
            except KeyError:
                raise RuntimeError('System call 0x{:02x} is not supported yet'.format(syscall))
        else:
            raise RuntimeError('Interrupt 0x{:02x} is not supported yet'.format(code))
