import sys
import operator
from functools import partial as P
from unittest.mock import MagicMock

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

    Functions that begin with a single underscore implement a single instruction, and for each mnemonic (e.g. `mov`, `add`)
    there must be only one corresponding function called `_<mnemonic>` that should accept only one argument - the opcode.
    Each of these functions must return `True` if the opcode equals one of the `valid_op`codes and `False` otherwise.

    Example:
        def _mnemonic(self, op: int) -> bool:
            valid_op = {  # valid opcodes
                0xAB: P(self.mnemonic_implementation1, value1, value2, test1=value3),  # all the arguments are provided at once
                0xBC: P(self.mnemonic_implementation2, value4, test2=value5),
                # and so on
            }

            # this part is the same for all mnemonics
            try:
                return valid_op[op]()
            except:
                return False
    """
    # TODO: implement MOV with sreg
    mov_rm_sreg = MagicMock(side_effect=RuntimeError('MOV does not support segment registers yet'))

    # TODO: implement far returns
    ret_far = MagicMock(side_effect=RuntimeError('RET far is not supported yet'))
    ret_far_imm = MagicMock(side_effect=RuntimeError('RET far imm is not supported yet'))
    
    # TODO: implement shifts
    shift = MagicMock(side_effect=RuntimeError('Shifts not implemented yet'))

    from .fetchLoop import execute_opcode, run, execute_bytes, execute_file, override
    from .misc import process_ModRM
    
    from .instructions import \
        mov_r_imm, mov_rm_imm, mov_rm_r, mov_r_rm, mov_r_moffs, \
        lea, \
        jmp_rel, jmp_rm, jmp_m, \
        call_rel, call_rm, call_m, \
        ret_near, ret_near_imm, \
        leave, \
        int_3, int_imm, \
        push_imm, push_r, push_rm, push_sreg, \
        pop_r, pop_rm, pop_sreg, \
        addsub_r_imm, addsub_rm_imm, addsub_rm_r, addsub_r_rm, \
        incdec_rm, incdec_r, \
        bitwise_r_imm, bitwise_rm_imm, bitwise_rm_r, bitwise_r_rm, \
        negnot_rm, \
        shift

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
        self.instr = {}
        
    def load_instructions(self):
    	if not self.instr:
    		self.instr = {
        	getattr(self, name) for name in dir(self) if name.startswith('_') and not name.startswith('__')
        	}

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

    def _mov(self, op: int):
        valid_op = {
            0xB0: P(self.mov_r_imm, op, _8bit=True),
            0xB8: P(self.mov_r_imm, op, _8bit=False),

            0xC6: P(self.mov_rm_imm, _8bit=True),
            0xC7: P(self.mov_rm_imm, _8bit=False),

            0x88: P(self.mov_rm_r, _8bit=True),
            0x89: P(self.mov_rm_r, _8bit=False),

            0x8A: P(self.mov_r_rm, _8bit=True),
            0x8B: P(self.mov_r_rm, _8bit=False),

            0x8C: P(self.mov_rm_sreg, reverse=False),
            0x8E: P(self.mov_rm_sreg, reverse=True),

            0xA0: P(self.mov_r_moffs, reverse=False, _8bit=True),
            0xA1: P(self.mov_r_moffs, reverse=False, _8bit=False),

            0xA2: P(self.mov_r_moffs, reverse=True, _8bit=True),
            0xA3: P(self.mov_r_moffs, reverse=True, _8bit=False),
        }

        for x in range(0xB1, 0xB8):
            valid_op[x] = valid_op[0xB0]

        for x in range(0xB8, 0xB8 + 8):
            valid_op[x] = valid_op[0xB8]

        try:
            return valid_op[op]()
        except:
            return False

    def _jmp(self, op: int):
        # TODO: implement jumps to pointers
        valid_op = {
            'rel8'  : [0xEB],
            'rel'   : [0xE9],
            'rm/m16': [0xFF],
            'ptr16' : [0xEA]
            }

        sz = self.sizes[self.current_mode]

        if op in valid_op['rel8']:
            self.jmp_rel(1)
        elif op in valid_op['rel']:
            self.jmp_rel(sz)
        elif op in valid_op['rm/m16']:
            if not self.jmp_rm(sz):
                return self.jmp_m(sz)
            return True
        elif op in valid_op['ptr16']:
            raise RuntimeError('Jumps to pointers not implemented yet')
        else:
            return False
        return True

    def _int(self, op: int):
        valid_op = {
            0xCC: P(self.int_3),
            0xCD: P(self.int_imm)
            }

        try:
            return valid_op[op]()
        except KeyError:
            return False

    def _push(self, op: int):
        valid_op = {
            0xFF: P(self.push_rm),
            0x50: P(self.push_r, op),

            0x6A: P(self.push_imm, _8bit=True),
            0x68: P(self.push_imm, _8bit=False),

            0x0E: P(self.push_sreg, 'CS'),
            0x16: P(self.push_sreg, 'SS'),
            0x1E: P(self.push_sreg, 'DS'),
            0x06: P(self.push_sreg, 'ES')
            }

        for x in range(0x51, 0x58):
            valid_op[x] = valid_op[0x50]

        if op == 0x0F:
            valid_op = {
                0xA0: P(self.push_sreg, 'FS'),
                0xA8: P(self.push_sreg, 'GS')
                }

            op = self.mem.get(self.eip, 1)
            self.eip += 1

        try:
            return valid_op[op]()
        except:
            return False

    def _pop(self, op: int):
        valid_op = {
            0x8F: P(self.pop_rm),
            0x58: P(self.pop_r, op),

            0x1F: P(self.pop_sreg, 'DS'),
            0x07: P(self.pop_sreg, 'ES'),
            0x17: P(self.pop_sreg, 'SS'),
            }

        for x in range(0x59, 0x58 + 8):
            valid_op[x] = valid_op[0x58]

        if op == 0x0F:
            valid_op = {
                0xA1: P(self.pop_sreg, 'FS', _32bit=True),
                0xA9: P(self.pop_sreg, 'GS', _32bit=True)
                }

            op = self.mem.get(self.eip, 1)
            self.eip += 1

        try:
            return valid_op[op]()
        except:
            return False

    def _call(self, op: int):
        # TODO: implement far calls
        valid_op = {
            'rel': [0xE8],
            'rm' : [0xFF],
            'ptr': [0x9A]
            }

        sz = self.sizes[self.current_mode]
        if op in valid_op['rel']:  # near, relative, displacement relative to next instr
            self.call_rel(sz)
        elif op in valid_op['rm']:
            if not self.call_rm(sz):
                return self.call_m(sz)
            return True
        elif op in valid_op['ptr']:
            raise RuntimeError("far calls (ptr) not implemented yet")
        else:
            return False
        return True

    def _ret(self, op: int):
        valid_op = {
            0xC3: P(self.ret_near),
            0xCB: P(self.ret_far),

            0xC2: P(self.ret_near_imm),
            0xCA: P(self.ret_far_imm)
            }

        try:
            return valid_op[op]()
        except:
            return False

    def _add(self, op: int):
        valid_op = {
            0x04: P(self.addsub_r_imm, _8bit=True),
            0x05: P(self.addsub_r_imm, _8bit=False),

            0x80: P(self.addsub_rm_imm, _8bit_op=True, _8bit_imm=True),
            0x81: P(self.addsub_rm_imm, _8bit_op=False, _8bit_imm=False),
            0x83: P(self.addsub_rm_imm, _8bit_op=False, _8bit_imm=True),

            0x00: P(self.addsub_rm_r, _8bit=True),
            0x01: P(self.addsub_rm_r, _8bit=False),
            0x02: P(self.addsub_r_rm, _8bit=True),
            0x03: P(self.addsub_r_rm, _8bit=False),
            }

        try:
            return valid_op[op]()
        except:
            return False

    def _sub(self, op: int):
        valid_op = {
            0x2C: P(self.addsub_r_imm, _8bit=True, sub=True),
            0x2D: P(self.addsub_r_imm, _8bit=False, sub=True),

            0x80: P(self.addsub_rm_imm, _8bit_op=True, _8bit_imm=True, sub=True),
            0x81: P(self.addsub_rm_imm, _8bit_op=False, _8bit_imm=False, sub=True),
            0x83: P(self.addsub_rm_imm, _8bit_op=False, _8bit_imm=True, sub=True),

            0x28: P(self.addsub_rm_r, _8bit=True, sub=True),
            0x29: P(self.addsub_rm_r, _8bit=False, sub=True),
            0x2A: P(self.addsub_r_rm, _8bit=True, sub=True),
            0x2B: P(self.addsub_r_rm, _8bit=False, sub=True),
            }

        try:
            return valid_op[op]()
        except:
            return False

    def _lea(self, op: int):
        valid_op = {
            0x8D: P(self.lea)
            }

        try:
            return valid_op[op]()
        except:
            return False

    def _cmp(self, op: int):
        valid_op = {
            0x3C: P(self.addsub_r_imm, _8bit=True, sub=True, cmp=True),
            0x3D: P(self.addsub_r_imm, _8bit=False, sub=True, cmp=True),

            0x80: P(self.addsub_rm_imm, _8bit_op=True, _8bit_imm=True, sub=True, cmp=True),
            0x81: P(self.addsub_rm_imm, _8bit_op=False, _8bit_imm=False, sub=True, cmp=True),
            0x83: P(self.addsub_rm_imm, _8bit_op=False, _8bit_imm=True, sub=True, cmp=True),

            0x38: P(self.addsub_rm_r, _8bit=True, sub=True, cmp=True),
            0x39: P(self.addsub_rm_r, _8bit=False, sub=True, cmp=True),
            0x3A: P(self.addsub_r_rm, _8bit=True, sub=True, cmp=True),
            0x3B: P(self.addsub_r_rm, _8bit=False, sub=True, cmp=True),
            }

        try:
            return valid_op[op]()
        except:
            return False

    def _jcc(self, op: int):
        valid_op = {
            'JPO': [123],
            'JNLE': [127],
            'JNC': [115],
            'JNL': [0x7D],
            'JNO': [113],
            'JNS': [121],
            'JPE': [122],
            'JO': [112],
            'JNGE': [124],
            'JECXZ': [227],
            'JNBE': [119],
            'JNZ': [117],
            'JZ': [116],
            'JS': [120],
            'JNA': [118],
            'JNG': [0x7E],
            'JNAE': [114]
            }
            
        sz = 1
        if op == 0x0F:
            for key, val in valid_op.items():
                valid_op[key] = [val[0] + 0x10]
            sz = self.sizes[self.current_mode]
            op = self.mem.get(self.eip, 1)[0]
            self.eip += 1
        	
        if op in valid_op['JPO']:
            if not self.reg.eflags_get(Reg32.PF):
                self.jmp_rel(sz)
            else:
                self.eip += sz  # pretend that we've read some bytes
        elif op in valid_op['JNLE']:
            if not self.reg.eflags_get(Reg32.PF) and self.reg.eflags_get(Reg32.SF) == self.reg.eflags_get(Reg32.OF):
                self.jmp_rel(sz)
            else:
                self.eip += sz
        elif op in valid_op['JNC']:
            if not self.reg.eflags_get(Reg32.CF):
                self.jmp_rel(sz)
            else:
                self.eip += sz
        elif op in valid_op['JNL']:
            if self.reg.eflags_get(Reg32.SF) == self.reg.eflags_get(Reg32.OF):
                self.jmp_rel(sz)
            else:
                self.eip += sz
        elif op in valid_op['JNO']:
            if not self.reg.eflags_get(Reg32.OF):
                self.jmp_rel(sz)
            else:
                self.eip += sz
        elif op in valid_op['JNS']:
            if not self.reg.eflags_get(Reg32.SF):
                self.jmp_rel(sz)
            else:
                self.eip += sz
        elif op in valid_op['JPE']:
            if self.reg.eflags_get(Reg32.PF):
                self.jmp_rel(sz)
            else:
                self.eip += sz
        elif op in valid_op['JO']:
            if self.reg.eflags_get(Reg32.PF):
                self.jmp_rel(sz)
            else:
                self.eip += sz
        elif op in valid_op['JNGE']:
            if self.reg.eflags_get(Reg32.SF) != self.reg.eflags_get(Reg32.OF):
                self.jmp_rel(sz)
            else:
                self.eip += sz
        elif op in valid_op['JECXZ']:
            if not to_int(self.reg.get(0, sz), byteorder):
                self.jmp_rel(sz)
            else:
                self.eip += sz
        elif op in valid_op['JNBE']:
            if not self.reg.eflags_get(Reg32.CF) and not self.reg.eflags_get(Reg32.ZF):
                self.jmp_rel(sz)
            else:
                self.eip += sz
        elif op in valid_op['JNZ']:
            if not self.reg.eflags_get(Reg32.ZF):
                self.jmp_rel(sz)
            else:
                self.eip += sz
        elif op in valid_op['JZ']:
            if self.reg.eflags_get(Reg32.ZF):
                self.jmp_rel(sz)
            else:
                self.eip += sz
        elif op in valid_op['JS']:
            if self.reg.eflags_get(Reg32.SF):
                self.jmp_rel(sz)
            else:
                self.eip += sz
        elif op in valid_op['JNA']:
            if self.reg.eflags_get(Reg32.CF) or self.reg.eflags_get(Reg32.ZF):
                self.jmp_rel(sz)
            else:
                self.eip += sz
        elif op in valid_op['JNG']:
            if self.reg.eflags_get(Reg32.ZF) or self.reg.eflags_get(Reg32.SF) != self.reg.eflags_get(Reg32.OF):
                self.jmp_rel(sz)
            else:
                self.eip += sz
        elif op in valid_op['JNAE']:
            if self.reg.eflags_get(Reg32.CF):
                self.jmp_rel(sz)
            else:
                self.eip += sz
        else:
            return False
        return True

    def _and(self, op: int):
        valid_op = {
            0x24: P(self.bitwise_r_imm, _8bit=True, operation=operator.and_),
            0x25: P(self.bitwise_r_imm, _8bit=False, operation=operator.and_),

            0x80: P(self.bitwise_rm_imm, _8bit=True, _8bit_imm=True, operation=operator.and_),
            0x81: P(self.bitwise_rm_imm, _8bit=False, _8bit_imm=False, operation=operator.and_),
            0x83: P(self.bitwise_rm_imm, _8bit=False, _8bit_imm=True, operation=operator.and_),

            0x20: P(self.bitwise_rm_r, _8bit=True, operation=operator.and_),
            0x21: P(self.bitwise_rm_r, _8bit=False, operation=operator.and_),

            0x22: P(self.bitwise_r_rm, _8bit=True, operation=operator.and_),
            0x23: P(self.bitwise_r_rm, _8bit=False, operation=operator.and_),
            }

        try:
            return valid_op[op]()
        except:
            return False

    def _or(self, op: int):
        valid_op = {
            0x0C: P(self.bitwise_r_imm, _8bit=True, operation=operator.or_),
            0x0D: P(self.bitwise_r_imm, _8bit=False, operation=operator.or_),

            0x80: P(self.bitwise_rm_imm, _8bit=True, _8bit_imm=True, operation=operator.or_),
            0x81: P(self.bitwise_rm_imm, _8bit=False, _8bit_imm=False, operation=operator.or_),
            0x83: P(self.bitwise_rm_imm, _8bit=False, _8bit_imm=True, operation=operator.or_),

            0x08: P(self.bitwise_rm_r, _8bit=True, operation=operator.or_),
            0x09: P(self.bitwise_rm_r, _8bit=False, operation=operator.or_),

            0x0A: P(self.bitwise_r_rm, _8bit=True, operation=operator.or_),
            0x0B: P(self.bitwise_r_rm, _8bit=False, operation=operator.or_),
            }

        try:
            return valid_op[op]()
        except:
            return False

    def _xor(self, op: int):
        valid_op = {
            0x34: P(self.bitwise_r_imm, _8bit=True, operation=operator.xor),
            0x35: P(self.bitwise_r_imm, _8bit=False, operation=operator.xor),

            0x80: P(self.bitwise_rm_imm, _8bit=True, _8bit_imm=True, operation=operator.xor),
            0x81: P(self.bitwise_rm_imm, _8bit=False, _8bit_imm=False, operation=operator.xor),
            0x83: P(self.bitwise_rm_imm, _8bit=False, _8bit_imm=True, operation=operator.xor),

            0x30: P(self.bitwise_rm_r, _8bit=True, operation=operator.xor),
            0x31: P(self.bitwise_rm_r, _8bit=False, operation=operator.xor),

            0x32: P(self.bitwise_r_rm, _8bit=True, operation=operator.xor),
            0x33: P(self.bitwise_r_rm, _8bit=False, operation=operator.xor),
            }

        try:
            return valid_op[op]()
        except:
            return False

    def _neg(self, op: int):
        valid_op = {
            0xF6: P(self.negnot_rm, _8bit=True, operation=0),
            0xF7: P(self.negnot_rm, _8bit=False, operation=0)
            }

        try:
            return valid_op[op]()
        except:
            return False

    def _not(self, op: int):
        valid_op = {
            0xF6: P(self.negnot_rm, _8bit=True, operation=1),
            0xF7: P(self.negnot_rm, _8bit=False, operation=1)
            }

        try:
            return valid_op[op]()
        except:
            return False

    def _test(self, op: int):
        valid_op = {
            0xA8: P(self.bitwise_r_imm, _8bit=True, operation=operator.and_, test=True),
            0xA9: P(self.bitwise_r_imm, _8bit=False, operation=operator.and_, test=True),

            0xF6: P(self.bitwise_rm_imm, _8bit=True, _8bit_imm=True, operation=operator.and_, test=True),
            0xF7: P(self.bitwise_rm_imm, _8bit=False, _8bit_imm=False, operation=operator.and_, test=True),

            0x84: P(self.bitwise_rm_r, _8bit=True, operation=operator.and_, test=True),
            0x85: P(self.bitwise_rm_r, _8bit=False, operation=operator.and_, test=True),
            }

        try:
            return valid_op[op]()
        except:
            return False

    def _inc(self, op: int):
        valid_op = {
            0xFE: P(self.incdec_rm, _8bit=True),
            0xFF: P(self.incdec_rm, _8bit=False),

            0x40: P(self.incdec_r, op, _8bit=False)
            }

        for x in range(0x41, 0x48):
            valid_op[x] = valid_op[0x40]

        try:
            return valid_op[op]()
        except:
            return False

    def _dec(self, op: int):
        valid_op = {
            0xFE: P(self.incdec_rm, _8bit=True, dec=True),
            0xFF: P(self.incdec_rm, _8bit=False, dec=True),

            0x48: P(self.incdec_r, op, _8bit=False, dec=True)
            }

        for x in range(0x49, 0x48 + 8):
            valid_op[x] = valid_op[0x48]

        try:
            return valid_op[op]()
        except:
            return False

    def _adc(self, op: int):
        valid_op = {
            0x14: P(self.addsub_r_imm, _8bit=True, carry=True),
            0x15: P(self.addsub_r_imm, _8bit=False, carry=True),

            0x80: P(self.addsub_rm_imm, _8bit_op=True, _8bit_imm=True, carry=True),
            0x81: P(self.addsub_rm_imm, _8bit_op=False, _8bit_imm=False, carry=True),
            0x83: P(self.addsub_rm_imm, _8bit_op=False, _8bit_imm=True, carry=True),

            0x10: P(self.addsub_rm_r, _8bit=True, carry=True),
            0x11: P(self.addsub_rm_r, _8bit=False, carry=True),
            0x12: P(self.addsub_r_rm, _8bit=True, carry=True),
            0x13: P(self.addsub_r_rm, _8bit=False, carry=True),
            }

        try:
            return valid_op[op]()
        except:
            return False

    def _sbb(self, op: int):
        valid_op = {
            0x1C: P(self.addsub_r_imm, _8bit=True, sub=True, carry=True),
            0x1D: P(self.addsub_r_imm, _8bit=False, sub=True, carry=True),

            0x80: P(self.addsub_rm_imm, _8bit_op=True, _8bit_imm=True, sub=True, carry=True),
            0x81: P(self.addsub_rm_imm, _8bit_op=False, _8bit_imm=False, sub=True, carry=True),
            0x83: P(self.addsub_rm_imm, _8bit_op=False, _8bit_imm=True, sub=True, carry=True),

            0x18: P(self.addsub_rm_r, _8bit=True, sub=True, carry=True),
            0x19: P(self.addsub_rm_r, _8bit=False, sub=True, carry=True),
            0x1A: P(self.addsub_r_rm, _8bit=True, sub=True, carry=True),
            0x1B: P(self.addsub_r_rm, _8bit=False, sub=True, carry=True),
            }

        try:
            return valid_op[op]()
        except:
            return False

    def _leave(self, op: int):
        valid_op = {
            0xC9: P(self.leave)
            }

        try:
            return valid_op[op]()
        except:
            return False
            
    def do_shift(self, op: int, operation):
    	valid_op = {
    		0xD0: P(self.shift, operation=operation, cnt=Shift.C_ONE, _8bit=True),
    		0xD2: P(self.shift, operation=operation, cnt=Shift.C_CL, _8bit=True),
    		0xC0: P(self.shift, operation=operation, cnt=Shift.C_imm8, _8bit=True),
    		
    		0xD1: P(self.shift, operation=operation, cnt=Shift.C_ONE, _8bit=False),
    		0xD3: P(self.shift, operation=operation, cnt=Shift.C_CL, _8bit=False),
    		0xC1: P(self.shift, operation=operation, cnt=Shift.C_imm8, _8bit=False)
    	}
    	
    	try:
    		return valid_op[op]()
    	except:
    		return False
    		
    def _shl(self, op: int):
    	return self.do_shift(op, Shift.SHL)
    	
    def _shr(self, op: int):
    	return self.do_shift(op, Shift.SHR)
    	
    def _sar(self, op: int):
    	return self.do_shift(op, Shift.SAR)
    	
    def _clc(self, op: int):
    	valid_op = {
    		0xF8: P(self.reg.eflags_set, Reg32.CF, 0)
    	}
    	
    	try:
    		return valid_op[op]()
    	except:
    		return False
    		
    def _cld(self, op: int):
    	valid_op = {
    		0xFC: P(self.reg.eflags_set, Reg32.DF, 0)
    	}
    	
    	try:
    		return valid_op[op]()
    	except:
    		return False
    		
    def _stc(self, op: int):
    	valid_op = {
    		0xF9: P(self.reg.eflags_set, Reg32.CF, 1)
    	}
    	
    	try:
    		return valid_op[op]()
    	except:
    		return False
    		
    def _std(self, op: int):
    	valid_op = {
    		0xFD: P(self.reg.eflags_set, Reg32.DF, 1)
    	}
    	
    	try:
    		return valid_op[op]()
    	except:
    		return False
