from .Memory import Memory
from .Registers import Reg32
from .util import CPU, byteorder, to_int

from . import instructions # this line MUST be here for the instructions to be loaded correctly

eax, ecx, edx, ebx, esp, ebp, esi, edi = range(8)


class CPU32(CPU):
    def __init__(self, memsize: int):
        super().__init__()

        self.mem = Memory(memsize)  # stack grows downward, user memory - upward
        self.reg = Reg32()

        self.eip = 0
        self.reg.set(esp, (memsize - 1).to_bytes(4, byteorder))
        self.reg.set(ebp, (memsize - 1).to_bytes(4, byteorder))

        self.code_segment_end = 0

    def stack_push(self, value: bytes) -> None:
        size = len(value)

        new_esp = to_int(self.reg.get(esp, 4)) - size

        if new_esp < self.code_segment_end:
            raise RuntimeError("The stack cannot grow larger than {}".format(self.code_segment_end))

        self.mem.set(new_esp, value)
        self.reg.set(esp, new_esp.to_bytes(4, byteorder))

    def stack_pop(self, size: int) -> bytes:
        old_esp = to_int(self.reg.get(esp, 4))
        data = self.mem.get(old_esp, size)
        new_esp = (old_esp + size).to_bytes(4, byteorder)
        self.reg.set(esp, new_esp)

        return data
