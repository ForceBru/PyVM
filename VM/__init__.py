import sys

from .CPU import CPU32
from .kernel import Kernel
from .fetchLoop import FetchLoopMixin, ExecuteBytes, ExecuteFlat, ExecuteELF, ExecutionStrategy

__author__ = '@ForceBru'
__version__ = 0, 1, 0


class VM(CPU32, FetchLoopMixin):
    __slots__ = 'fmt', 'descriptors', 'GDT', 'running', 'RETCODE', 'kernel'
    from .misc import process_ModRM

    def __init__(self, memsize: int, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
        super().__init__(int(memsize))
        self.kernel = Kernel(self)

        self.descriptors = [stdin, stdout, stderr]
        self.GDT = [
            b'\0' * 8  # 64-bit entry
        ] * 6  # TODO: how many entries are there?
        self.RETCODE = None

    def interrupt(self, code: int):
        if code == 0x80:  # syscall
            syscall_number = self.reg.eax

            self.reg.eax = self.kernel[syscall_number]()
        else:
            raise RuntimeError(f'Interrupt 0x{code:02x} is not supported yet')


class VMKernel(VM, ExecuteELF, ExecuteBytes, ExecuteFlat):
    def execute(self, strategy: ExecutionStrategy, *args, **kwargs):
        bases = {
            ExecutionStrategy.BYTES: ExecuteBytes,
            ExecutionStrategy.FLAT: ExecuteFlat,
            ExecutionStrategy.ELF: ExecuteELF
        }

        return bases[strategy].execute(self, *args, **kwargs)
