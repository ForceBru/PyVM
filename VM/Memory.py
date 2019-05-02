from .util import SegmentRegs


class Memory:
    def __init__(self, size: int, reg: "registers"):
        self.memory = bytearray(size)
        self.bounds = range(size)
        self.segment_registers = reg
        self.size = size

        self.program_break = None
        self.__segment_override_type = SegmentRegs.DS
        self.__segment_override = self.segment_registers.sreg[self.__segment_override_type]

    def __test_bounds(self, offset: int, size: int, func_name: str):
        if offset not in self.bounds:
            if offset > self.bounds.stop:
                raise MemoryError(f"{func_name}: not enough memory (requested address: {offset}, memory available: {len(self.bounds)})")
            else:
                raise RuntimeError(f"{func_name}: invalid memory access (requested address: {offset}, memory bounds: {self.bounds})")

        offset += size

        if offset not in self.bounds:
            if offset > self.bounds.stop:
                raise MemoryError(f"{func_name}: not enough memory (requested address: {offset}, memory available: {len(self.bounds)})")
            else:
                raise RuntimeError(f"{func_name}: invalid memory access (requested address: {offset}, memory bounds: {self.bounds})")

    @property
    def segment_override(self):
        return self.__segment_override

    @segment_override.setter
    def segment_override(self, segment_type: SegmentRegs):
        self.__segment_override_type = segment_type
        self.__segment_override = self.segment_registers.sreg[segment_type]

    def size_set(self, size: int):
        if self.size >= size:
            return
            
        self.size_increase(size - self.size)
        
    def size_increase(self, size: int):
        self.memory += bytearray(size)
        self.size += size
        self.bounds = range(self.size)

    def get(self, offset: int, size: int) -> bytes:
        offset += self.__segment_override.base

        self.__test_bounds(offset, size, 'Memory.get')

        return self.memory[offset:offset + size]

    def get_eip(self, offset: int, size: int) -> bytes:
        self.__test_bounds(offset, size, 'Memory.get')

        return self.memory[offset:offset + size]

    def set(self, offset: int, value: bytes) -> None:
        size = len(value)
        offset += self.__segment_override.base

        self.__test_bounds(offset, size, 'Memory.set')

        self.memory[offset:offset + size] = value

    def fill(self, offset: int, value: int) -> None:
        self.__test_bounds(offset, 1, 'Memory.fill')
        assert value in range(256)

        for i in range(offset, self.bounds.stop):
            self.memory[i] = value
