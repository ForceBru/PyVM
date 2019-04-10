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
    from .fetchLoop import execute_opcode, run, execute_bytes, execute_file, execute_elf, override
    from .misc import process_ModRM

    from .kernel import sys_exit, sys_read, sys_write

    def __init__(self, memsize: int, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
        super().__init__(int(memsize))

        self.fmt = '\t[0x{:0' + str(len(str(self.mem.size))//16) + 'x}]: 0x{:02x}'

        self.descriptors = [stdin, stdout, stderr]
        self.RETCODE = None
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
