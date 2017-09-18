import sys

from .CPU import CPU32, to_int, byteorder
from .debug import debug

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

    The names of the functions in the `internals` module begin with `_VM__<function name>`, thus, they should be imported
    as `__<function name>`.

    Functions that begin with a single underscore implement a single instruction, and for each mnemonic (e.g. `mov`, `add`)
    there must be only one corresponding function called `_<mnemonic>` that should accept only one argument - the opcode.
    Each of these functions must return `True` if the opcode equals one of the `valid_op`codes and `False` otherwise.
    """
    from .fetchLoop import execute_opcode, run, execute_file
    from .misc import process_ModRM
    from .internals import \
        __mov_r_imm, __mov_rm_imm, __mov_rm_r, __mov_r_rm, __mov_eax_moffs, __mov_moffs_eax, \
        __jmp_rel, \
        __addsub_al_imm, __addsub_rm_imm, __addsub_rm_r, __addsub_r_rm

    from .kernel import __sys_exit, __sys_read, __sys_write

    def __init__(self, memsize):
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

        if code not in valid_codes:
            raise RuntimeError('Invalid interrupt: {}'.format(hex(code)))

        if code == valid_codes[0]:  # syscall
            valid_syscalls = {
                0x1: self.__sys_exit,
                0x3: self.__sys_read,
                0x4: self.__sys_write
                }

            syscall = to_int(self.reg.get(0, 4))  # EAX

            valid_syscalls[syscall]()
        else:
            ...

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
            self.__mov_r_imm(1, op)
        elif op in valid_op['r,imm']:
            self.__mov_r_imm(sz, op)
        elif op in valid_op['rm8,imm8']:
            return self.__mov_rm_imm(1)
        elif op in valid_op['rm,imm']:
            return self.__mov_rm_imm(sz)
        elif op in valid_op['rm8,r8']:
            self.__mov_rm_r(1)
        elif op in valid_op['rm,r']:
            self.__mov_rm_r(sz)
        elif op in valid_op['r8,rm8']:
            self.__mov_r_rm(1)
        elif op in valid_op['r,rm']:
            self.__mov_r_rm(sz)
        elif op in valid_op['rm16,sreg']:
            raise RuntimeError('Segment registers not implemented yet')
        elif op in valid_op['sreg,rm16']:
            raise RuntimeError('Segment registers not implemented yet')
        elif op in valid_op['al,moffs8']:
            # TODO: I should be reading 1 byte here, but NASM outputs a bit-switch byte and 4-bytes moffs. WTF??
            self.__mov_eax_moffs(1)
        elif op in valid_op['ax,moffs']:
            self.__mov_eax_moffs(sz)
        elif op in valid_op['moffs8,al']:
            self.__mov_moffs_eax(1)
        elif op in valid_op['moffs,ax']:
            self.__mov_moffs_eax(sz)
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
            self.__jmp_rel(1)
        elif op in valid_op['rel']:
            self.__jmp_rel(sz)
        elif op in valid_op['rm/m16']:
            RM, R = self.process_ModRM(sz, sz)

            if R[1] == 4:  # R/M
                d = self.mem.get(self.eip, sz)
                self.eip = to_int(d) & ((1 << sz * 8) - 1)
                debug('jmp rm{}({})'.format(sz * 8, self.eip))
            elif R[1] == 5:  # M
                _d = self.mem.get(self.eip, sz)
                _d = to_int(_d)
                d = self.mem.get(_d, sz)
                self.eip = to_int(d) & ((1 << sz * 8) - 1)
                debug('jmp m{}({})'.format(sz * 8, self.eip))
            else:
                return False
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
            sys.stderr.write("[!] It's a trap! (literally)")
        elif op in valid_op['imm8']:
            imm = self.mem.get(self.eip, 1)
            imm = to_int(imm)
            self.eip += 1

            self.interrupt(imm)
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
            RM, R = self.process_ModRM(sz, sz)

            if R[1] != 6:
                return False

            type, loc, _ = RM

            if not type:
                data = self.reg.get(loc, sz)
                debug('push r{}({})'.format(sz * 8, data))
            else:
                # relative address!
                data = self.mem.get(loc, sz)
                debug('push m{}({})'.format(sz * 8, data))

            self.stack_push(data)
        elif op in valid_op['r']:
            loc = op & 0b111
            data = self.reg.get(loc, sz)
            debug('push r{}({})'.format(sz * 8, loc))
            self.stack_push(data)
        elif op in valid_op['imm8']:
            data = self.mem.get(self.eip, 1)
            self.eip += 1
            debug('push imm8({})'.format(data))
            self.stack_push(data)
        elif op in valid_op['imm']:
            data = self.mem.get(self.eip, sz)
            self.eip += sz
            debug('push imm{}({})'.format(sz * 8, data))
            self.stack_push(data)
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
            RM, R = self.process_ModRM(sz, sz)

            if R[1] != 0:
                return False

            type, loc, _ = RM
            data = self.stack_pop(sz)

            if not type:
                self.reg.set(loc, data)
                debug('pop _r{}({})'.format(sz * 8, data))
            else:
                self.reg.set(loc, data)
                debug('pop m{}({})'.format(sz * 8, data))
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
            dest = self.mem.get(self.eip, sz)
            self.eip += sz
            dest = to_int(dest, True) & ((1 << sz * 8) - 1)
            tmpEIP = self.eip + dest

            self.stack_push(self.eip.to_bytes(sz, CPU.byteorder, signed=True))
            self.eip = tmpEIP
            debug("call rel{}({})".format(sz * 8, self.eip))
        elif op in valid_op['rm']:
            RM, R = self.process_ModRM(sz, sz)

            type, loc, _ = RM

            if R[1] == 2:  # near, abs, indirect, addr in r/m
                if not type:
                    dest = self.reg.get(loc, sz)
                else:
                    dest = self.mem.get(loc, sz)
                tmpEIP = to_int(dest, True) & ((1 << sz * 8) - 1)
                self.stack_push(self.eip.to_bytes(sz, CPU.byteorder, signed=True))
                self.eip = tmpEIP
                debug("call {}{}({})".format('rm'[type], sz * 8, self.eip))
            elif R[1] == 3:  # far, abs, indirect, addr in m
                raise RuntimeError("far calls (mem) not implemented yet")
            else:
                return False
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
            self.eip = to_int(self.stack_pop(sz), True) & ((1 << sz * 8) - 1)
            debug("ret ({})".format(self.eip))
        elif op in valid_op['near_imm']:
            self.eip = to_int(self.stack_pop(sz), True) & ((1 << sz * 8) - 1)
            nbytes_to_pop = self.mem.get(self.eip, sz)
            nbytes_to_pop = to_int(nbytes_to_pop)
            self.eip += sz
            self.stack_pop(nbytes_to_pop)
        elif op in valid_op['far']:
            raise RuntimeError("far returns not implemented yet")
        elif op in valid_op['far_imm']:
            raise RuntimeError("far returns (imm) not implemented yet")
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
            self.__addsub_al_imm(1)
        elif op in valid_op['ax,imm']:
            self.__addsub_al_imm(sz)
        elif op in valid_op['rm8,imm8']:
            return self.__addsub_rm_imm(1, 1)
        elif op in valid_op['rm,imm']:
            return self.__addsub_rm_imm(sz, sz)
        elif op in valid_op['rm,imm8']:
            return self.__addsub_rm_imm(sz, 1)
        elif op in valid_op['rm8,r8']:
            self.__addsub_rm_r(1)
        elif op in valid_op['rm,r']:
            self.__addsub_rm_r(sz)
        elif op in valid_op['r8,rm8']:
            self.__addsub_r_rm(1)
        elif op in valid_op['r,rm']:
            self.__addsub_r_rm(sz)
        else:
            return False
        return True

    def _sub(self, op: int):
        # TODO: handle overflows
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
            self.__addsub_al_imm(1, True)
        elif op in valid_op['ax,imm']:
            self.__addsub_al_imm(sz, True)
        elif op in valid_op['rm8,imm8']:
            return self.__addsub_rm_imm(1, 1, True)
        elif op in valid_op['rm,imm']:
            return self.__addsub_rm_imm(sz, sz, True)
        elif op in valid_op['rm,imm8']:
            return self.__addsub_rm_imm(sz, 1, True)
        elif op in valid_op['rm8,r8']:
            self.__addsub_rm_r(1, True)
        elif op in valid_op['rm,r']:
            self.__addsub_rm_r(sz, True)
        elif op in valid_op['r8,rm8']:
            self.__addsub_r_rm(1, True)
        elif op in valid_op['r,rm']:
            self.__addsub_r_rm(sz, True)
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