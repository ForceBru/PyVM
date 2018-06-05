import sys
import operator
from functools import partial as P

from .CPU import CPU32
from .util import to_int, byteorder
from .debug import debug
from .Registers import Reg32
from .misc import Shift


class VM(CPU32):
    # TODO: this stuff looks ugly, refactor it
    from .fetchLoop import execute_opcode, run, execute_bytes, execute_file, override
    from .misc import process_ModRM

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