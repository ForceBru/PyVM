from .Memory import Memory
from .Registers import Reg32, FReg32
from .util import CPU, byteorder, to_int

from . import instructions  # this line MUST be here for the instructions to be loaded correctly

eax, ecx, edx, ebx, esp, ebp, esi, edi = range(8)


class CPU32(CPU):
    def __init__(self, memsize: int):
        super().__init__()

        self.reg = Reg32()
        self.freg = FReg32()
        self.mem = Memory(memsize, self.reg)  # stack grows downward, user memory - upward

        self.eip = 0

        self.modes = (32, 16)  # number of bits
        self.sizes = (4, 2)  # number of bytes
        self.default_mode = 0  # 0 == 32-bit mode; 1 == 16-bit mode
        self.current_mode = self.default_mode

        self.operand_size = self.sizes[self.current_mode]
        self.address_size = self.sizes[self.current_mode]
        self.stack_address_size = self.sizes[self.current_mode]

        self.code_segment_end = 0
        self.stack_init()
        
    def stack_init(self):
        self.reg.set(esp, (self.mem.size - 1).to_bytes(4, byteorder))
        self.reg.set(ebp, (self.mem.size - 1).to_bytes(4, byteorder))

    def stack_push(self, value: bytes) -> None:
        new_esp = to_int(self.reg.get(esp, self.stack_address_size)) - self.operand_size

        if new_esp < self.mem.program_break:
            raise RuntimeError(f"The stack cannot grow larger than {self.mem.program_break}")

        self.mem.set(new_esp, value)
        self.reg.set(esp, new_esp.to_bytes(self.stack_address_size, byteorder))

    def stack_pop(self, size: int) -> bytes:
        old_esp = to_int(self.reg.get(esp, self.stack_address_size))

        data = self.mem.get(old_esp, size)
        new_esp = (old_esp + size).to_bytes(self.stack_address_size, byteorder)
        self.reg.set(esp, new_esp)

        return data
