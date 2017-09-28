import sys
import operator

from .CPU import CPU32, to_int, byteorder
from .debug import debug
from .Registers import Reg32

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
    """
    from .fetchLoop import execute_opcode, run, execute_bytes, execute_file
    from .misc import process_ModRM
    
    from .instructions import \
        mov_r_imm, mov_rm_imm, mov_rm_r, mov_r_rm, mov_eax_moffs, mov_moffs_eax, \
        jmp_rel, jmp_rm, jmp_m, \
        call_rel, call_rm, call_m, \
        ret_near, ret_near_imm, ret_far, ret_far_imm, \
        int_3, int_imm, \
        push_imm, push_rm, pop_rm, \
        addsub_al_imm, addsub_rm_imm, addsub_rm_r, addsub_r_rm, \
        incdec_rm, incdec_r, \
        bitwise_al_imm, bitwise_rm_imm, bitwise_rm_r, bitwise_r_rm, \
        negnot_rm

    from .kernel import sys_exit, sys_read, sys_write

    def __init__(self, memsize: int):
        super().__init__(memsize)

        self.modes = (32, 16)  # number of bits
        self.sizes = (4, 2)  # number of bytes
        self.default_mode = 0  # 0 == 32-bit mode; 1 == 16-bit mode
        self.current_mode = self.default_mode
        self.operand_size = self.sizes[self.current_mode]
        self.address_size = self.sizes[self.current_mode]

        self.fmt = '\t[0x{:0' + str(len(str(self.mem.size))//16) + 'x}]: 0x{:02x}'

        self.descriptors = [sys.stdin, sys.stdout, sys.stderr]
        self.running = True

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
            'r8,imm8'  : range(0xB0, 0xB8),
            'r,imm'    : range(0xB8, 0xB8 + 8),
            'rm8,imm8' : [0xC6],
            'rm,imm'   : [0xC7],

            'rm8,r8'   : [0x88],
            'rm,r'     : [0x89],
            'r8,rm8'   : [0x8A],
            'r,rm'     : [0x8B],
            'rm16,sreg': [0x8C],
            'sreg,rm16': [0x8E],

            'al,moffs8': [0xA0],
            'ax,moffs' : [0xA1],
            'moffs8,al': [0xA2],
            'moffs,ax' : [0xA3]
            }

        sz = self.sizes[self.current_mode]

        if op in valid_op['r8,imm8']:
            self.mov_r_imm(1, op)
        elif op in valid_op['r,imm']:
            self.mov_r_imm(sz, op)
        elif op in valid_op['rm8,imm8']:
            return self.mov_rm_imm(1)
        elif op in valid_op['rm,imm']:
            return self.mov_rm_imm(sz)
        elif op in valid_op['rm8,r8']:
            self.mov_rm_r(1)
        elif op in valid_op['rm,r']:
            self.mov_rm_r(sz)
        elif op in valid_op['r8,rm8']:
            self.mov_r_rm(1)
        elif op in valid_op['r,rm']:
            self.mov_r_rm(sz)
        elif op in valid_op['rm16,sreg']:
            raise RuntimeError('Segment registers not implemented yet')
        elif op in valid_op['sreg,rm16']:
            raise RuntimeError('Segment registers not implemented yet')
        elif op in valid_op['al,moffs8']:
            self.mov_eax_moffs(1)
        elif op in valid_op['ax,moffs']:
            self.mov_eax_moffs(sz)
        elif op in valid_op['moffs8,al']:
            self.mov_moffs_eax(1)
        elif op in valid_op['moffs,ax']:
            self.mov_moffs_eax(sz)
        else:
            return False
        return True

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
            '3'   : [0xCC],
            'imm8': [0xCD]
            }

        if op in valid_op['3']:
            self.int_3(0)
        elif op in valid_op['imm8']:
            self.int_imm(1)
        else:
            return False
        return True

    def _push(self, op: int):
        valid_op = {
            'rm'  : [0xFF],
            'r'   : range(0x50, 0x58),
            'imm8': [0x6A],
            'imm' : [0x68]
            # segment registers not supported
            }

        sz = self.sizes[self.current_mode]
        if op in valid_op['rm']:
            return self.push_rm(sz)
        elif op in valid_op['r']:
            loc = op & 0b111
            data = self.reg.get(loc, sz)
            debug('push r{}({})'.format(sz * 8, loc))
            self.stack_push(data)
        elif op in valid_op['imm8']:
            self.push_imm(1)
        elif op in valid_op['imm']:
            self.push_imm(sz)
        else:
            return False
        return True

    def _pop(self, op: int):
        valid_op = {
            'rm': [0x8F],
            'r' : range(0x58, 0x58 + 8)
            # segment registers not supported
            }

        sz = self.sizes[self.current_mode]
        if op in valid_op['rm']:
            return self.pop_rm(sz)
        elif op in valid_op['r']:
            loc = op & 0b111
            data = self.stack_pop(sz)
            self.reg.set(loc, data)
            debug('pop r{}({})'.format(sz * 8, loc))
        else:
            return False
        return True

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
        # TODO: implement far returns
        valid_op = {
            'near'    : [0xC3],
            'far'     : [0xCB],
            'near_imm': [0xC2],
            'far_imm' : [0xCA]
            }

        sz = self.sizes[self.current_mode]
        if op in valid_op['near']:
            self.ret_near(sz)
        elif op in valid_op['near_imm']:
            self.ret_near_imm(sz)
        elif op in valid_op['far']:
            self.ret_far(sz)
        elif op in valid_op['far_imm']:
            self.ret_far_imm(sz)
        else:
            return False
        return True

    def _add(self, op: int):
        # TODO: handle overflows
        valid_op = {
            'al,imm8' : [0x04],
            'ax,imm'  : [0x05],
            'rm8,imm8': [0x80],
            'rm,imm'  : [0x81],
            'rm,imm8' : [0x83],
            'rm8,r8'  : [0x00],
            'rm,r'    : [0x01],
            'r8,rm8'  : [0x02],
            'r,rm'    : [0x03]
            }

        sz = self.sizes[self.current_mode]
        if op in valid_op['al,imm8']:
            self.addsub_al_imm(1)
        elif op in valid_op['ax,imm']:
            self.addsub_al_imm(sz)
        elif op in valid_op['rm8,imm8']:
            return self.addsub_rm_imm(1, 1)
        elif op in valid_op['rm,imm']:
            return self.addsub_rm_imm(sz, sz)
        elif op in valid_op['rm,imm8']:
            return self.addsub_rm_imm(sz, 1)
        elif op in valid_op['rm8,r8']:
            self.addsub_rm_r(1)
        elif op in valid_op['rm,r']:
            self.addsub_rm_r(sz)
        elif op in valid_op['r8,rm8']:
            self.addsub_r_rm(1)
        elif op in valid_op['r,rm']:
            self.addsub_r_rm(sz)
        else:
            return False
        return True

    def _sub(self, op: int):
        valid_op = {
            'al,imm8' : [0x2C],
            'ax,imm'  : [0x2D],
            'rm8,imm8': [0x80],
            'rm,imm'  : [0x81],
            'rm,imm8' : [0x83],
            'rm8,r8'  : [0x28],
            'rm,r'    : [0x29],
            'r8,rm8'  : [0x2A],
            'r,rm'    : [0x2B]
            }

        sz = self.sizes[self.current_mode]
        if op in valid_op['al,imm8']:
            self.addsub_al_imm(1, True)
        elif op in valid_op['ax,imm']:
            self.addsub_al_imm(sz, True)
        elif op in valid_op['rm8,imm8']:
            return self.addsub_rm_imm(1, 1, True)
        elif op in valid_op['rm,imm']:
            return self.addsub_rm_imm(sz, sz, True)
        elif op in valid_op['rm,imm8']:
            return self.addsub_rm_imm(sz, 1, True)
        elif op in valid_op['rm8,r8']:
            self.addsub_rm_r(1, True)
        elif op in valid_op['rm,r']:
            self.addsub_rm_r(sz, True)
        elif op in valid_op['r8,rm8']:
            self.addsub_r_rm(1, True)
        elif op in valid_op['r,rm']:
            self.addsub_r_rm(sz, True)
        else:
            return False
        return True

    def _lea(self, op: int):
        valid_op = {
            'r,m': [0x8D]
            }

        if op in valid_op['r,m']:
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
        else:
            return False
        return True

    def _cmp(self, op: int):
        valid_op = {
            'al,imm8': [0x3C],
            'ax,imm': [0x3D],
            'rm8,imm8': [0x80],
            'rm,imm': [0x81],
            'rm,imm8': [0x83],
            'rm8,r8': [0x38],
            'rm,r': [0x39],
            'r8,rm8': [0x3A],
            'r,rm': [0x3B]
            }

        sz = self.sizes[self.current_mode]
        if op in valid_op['al,imm8']:
            self.addsub_al_imm(1, True, True)
        elif op in valid_op['ax,imm']:
            self.addsub_al_imm(sz, True, True)
        elif op in valid_op['rm8,imm8']:
            return self.addsub_rm_imm(1, 1, True, True)
        elif op in valid_op['rm,imm']:
            return self.addsub_rm_imm(sz, sz, True, True)
        elif op in valid_op['rm,imm8']:
            return self.addsub_rm_imm(sz, 1, True, True)
        elif op in valid_op['rm8,r8']:
            self.addsub_rm_r(1, True, True)
        elif op in valid_op['rm,r']:
            self.addsub_rm_r(sz, True, True)
        elif op in valid_op['r8,rm8']:
            self.addsub_r_rm(1, True, True)
        elif op in valid_op['r,rm']:
            self.addsub_r_rm(sz, True, True)
        else:
            return False
        return True

    def _jcc(self, op: int):
        valid_op = {
            'JPO': [123],
            'JNLE': [127],
            'JNC': [115], # TODO: carry
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
            'al,imm8': [0x24],
            'ax,imm': [0x25],
            'rm8,imm8': [0x80],
            'rm,imm': [0x81],
            'rm,imm8': [0x83],
            'rm8,r8': [0x20],
            'rm,r': [0x21],
            'r8,rm8': [0x22],
            'r,rm': [0x23]
            }

        sz = self.sizes[self.current_mode]
        if op in valid_op['al,imm8']:
            self.bitwise_al_imm(1, operator.and_)
        elif op in valid_op['ax,imm']:
            self.bitwise_al_imm(sz, operator.and_)
        elif op in valid_op['rm8,imm8']:
            return self.bitwise_rm_imm(1, 1, operator.and_)
        elif op in valid_op['rm,imm']:
            return self.bitwise_rm_imm(sz, sz, operator.and_)
        elif op in valid_op['rm,imm8']:
            return self.bitwise_rm_imm(sz, 1, operator.and_)
        elif op in valid_op['rm8,r8']:
            self.bitwise_rm_r(1, operator.and_)
        elif op in valid_op['rm,r']:
            self.bitwise_rm_r(sz, operator.and_)
        elif op in valid_op['r8,rm8']:
            self.bitwise_rm_r(1, operator.and_)
        elif op in valid_op['r,rm']:
            self.bitwise_rm_r(sz, operator.and_)
        else:
            return False
        return True

    def _or(self, op: int):
        valid_op = {
            'al,imm8': [0x0C],
            'ax,imm': [0x0D],
            'rm8,imm8': [0x80],
            'rm,imm': [0x81],
            'rm,imm8': [0x83],
            'rm8,r8': [0x08],
            'rm,r': [0x09],
            'r8,rm8': [0x0A],
            'r,rm': [0x0B]
            }

        sz = self.sizes[self.current_mode]
        if op in valid_op['al,imm8']:
            self.bitwise_al_imm(1, operator.or_)
        elif op in valid_op['ax,imm']:
            self.bitwise_al_imm(sz, operator.or_)
        elif op in valid_op['rm8,imm8']:
            return self.bitwise_rm_imm(1, 1, operator.or_)
        elif op in valid_op['rm,imm']:
            return self.bitwise_rm_imm(sz, sz, operator.or_)
        elif op in valid_op['rm,imm8']:
            return self.bitwise_rm_imm(sz, 1, operator.or_)
        elif op in valid_op['rm8,r8']:
            self.bitwise_rm_r(1, operator.or_)
        elif op in valid_op['rm,r']:
            self.bitwise_rm_r(sz, operator.or_)
        elif op in valid_op['r8,rm8']:
            self.bitwise_rm_r(1, operator.or_)
        elif op in valid_op['r,rm']:
            self.bitwise_rm_r(sz, operator.or_)
        else:
            return False
        return True

    def _xor(self, op: int):
        valid_op = {
            'al,imm8': [0x34],
            'ax,imm': [0x35],
            'rm8,imm8': [0x80],
            'rm,imm': [0x81],
            'rm,imm8': [0x83],
            'rm8,r8': [0x30],
            'rm,r': [0x31],
            'r8,rm8': [0x32],
            'r,rm': [0x33]
            }

        sz = self.sizes[self.current_mode]
        if op in valid_op['al,imm8']:
            self.bitwise_al_imm(1, operator.xor)
        elif op in valid_op['ax,imm']:
            self.bitwise_al_imm(sz, operator.xor)
        elif op in valid_op['rm8,imm8']:
            return self.bitwise_rm_imm(1, 1, operator.xor)
        elif op in valid_op['rm,imm']:
            return self.bitwise_rm_imm(sz, sz, operator.xor)
        elif op in valid_op['rm,imm8']:
            return self.bitwise_rm_imm(sz, 1, operator.xor)
        elif op in valid_op['rm8,r8']:
            self.bitwise_rm_r(1, operator.xor)
        elif op in valid_op['rm,r']:
            self.bitwise_rm_r(sz, operator.xor)
        elif op in valid_op['r8,rm8']:
            self.bitwise_rm_r(1, operator.xor)
        elif op in valid_op['r,rm']:
            self.bitwise_rm_r(sz, operator.xor)
        else:
            return False
        return True

    def _neg(self, op: int):
        valid_op = {
            'rm8': [0xF8],
            'rm': [0xF7]
            }
        NEG = 0

        sz = self.sizes[self.current_mode]
        if op in valid_op['rm8']:
            return self.negnot_rm(1, NEG)
        elif op in valid_op['rm']:
            return self.negnot_rm(sz, NEG)
        else:
            return False

    def _not(self, op: int):
        valid_op = {
            'rm8': [0xF6],
            'rm': [0xF7]
            }

        NOT = 1

        sz = self.sizes[self.current_mode]
        if op in valid_op['rm8']:
            return self.negnot_rm(1, NOT)
        elif op in valid_op['rm']:
            return self.negnot_rm(sz, NOT)
        else:
            return False

    def _test(self, op: int):
        valid_op = {
            'al,imm8' : [0xA8],
            'ax,imm'  : [0xA9],
            'rm8,imm8': [0xF6],
            'rm,imm'  : [0xF7],
            'rm8,r8'  : [0x84],
            'rm,r'    : [0x85]
            }

        sz = self.sizes[self.current_mode]
        if op in valid_op['al,imm8']:
            self.bitwise_al_imm(1, operator.and_, True)
        elif op in valid_op['ax,imm']:
            self.bitwise_al_imm(sz, operator.and_, True)
        elif op in valid_op['rm8,imm8']:
            return self.bitwise_rm_imm(1, 1, operator.and_, True)
        elif op in valid_op['rm,imm']:
            return self.bitwise_rm_imm(sz, sz, operator.and_, True)
        elif op in valid_op['rm8,r8']:
            self.bitwise_rm_r(1, operator.and_, True)
        elif op in valid_op['rm,r']:
            self.bitwise_rm_r(sz, operator.and_, True)
        else:
            return False
        return True
        
    
    def _inc(self, op: int):
        valid_op = {
            'rm8': [0xFE],
            'rm' : [0xFF],
            'r'  : range(0x40, 0x48)
        }
        
        sz = self.sizes[self.current_mode]
        if op in valid_op['rm8']:
            return self.incdec_rm(1)
        elif op in valid_op['rm']:
            return self.incdec_rm(sz)
        elif op in valid_op['r']:
            self.incdec_r(sz, op)
        else:
            return False
        return True
    
    
    def _dec(self, op: int):
        valid_op = {
            'rm8': [0xFE],
            'rm' : [0xFF],
            'r'  : range(0x48, 0x50)
        }
        
        sz = self.sizes[self.current_mode]
        if op in valid_op['rm8']:
            return self.incdec_rm(1, dec=True)
        elif op in valid_op['rm']:
            return self.incdec_rm(sz, dec=True)
        elif op in valid_op['r']:
            self.incdec_r(sz, op, dec=True)
        else:
            return False
        return True
