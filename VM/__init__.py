import sys
import collections

from .CPU import CPU32
from .util import to_int, byteorder
from .debug import debug
from .Registers import Reg32
from .misc import Shift
from .kernel import SyscallsMixin


class VM(CPU32, SyscallsMixin):
    # TODO: this stuff looks ugly, refactor it
    from .fetchLoop import execute_opcode, run, execute_bytes, execute_file, execute_elf, override
    from .misc import process_ModRM

    def __init__(self, memsize: int, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
        super().__init__(int(memsize))

        #self.fmt = '\t[0x{:0' + str(len(str(self.mem.size))//16) + 'x}]: 0x{:02x}'
        self.fmt = f'\t[0x%08x]\t%x'

        self.descriptors = [stdin, stdout, stderr]
        self.GDT = [
            b'\0' * 8  # 64-bit entry
        ] * 6  # TODO: how many entries are there?
        self.valid_syscalls = {
            code: getattr(self, name)
            for code, name in self.valid_syscalls_names.items()
        }
        self.RETCODE = None
        self.running = True

    def interrupt(self, code: int):
        valid_codes = [0x80]

        if code == valid_codes[0]:  # syscall
            syscall = self.reg.get(0, 4)  # EAX

            try:
                self.valid_syscalls[syscall]()
            except KeyError:
                raise RuntimeError('System call 0x{:02x} is not supported yet'.format(syscall))
        else:
            raise RuntimeError('Interrupt 0x{:02x} is not supported yet'.format(code))
