import sys

from .CPU import CPU32
from .kernel import SyscallsMixin


class VM(CPU32, SyscallsMixin):
    # TODO: this stuff looks ugly, refactor it
    from .fetchLoop import execute_opcode, run, execute_bytes, execute_file, execute_elf
    from .misc import process_ModRM

    def __init__(self, memsize: int, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
        super().__init__(int(memsize))

        self.fmt = f'\t[0x%08x]\t%02x'

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
        if code == 0x80:  # syscall
            syscall_number = self.reg.eax
            syscall_impl = self.valid_syscalls.get(syscall_number)

            if syscall_impl is None:
                raise RuntimeError(f'System call 0x{syscall_number:02x} is not supported yet')

            syscall_impl()
        else:
            raise RuntimeError(f'Interrupt 0x{code:02x} is not supported yet')
