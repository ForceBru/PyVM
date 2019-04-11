class Memory:
    def __init__(self, size: int):
        self.memory = bytearray(size)
        self.bounds = range(size)
        self.size = size
        self.program_break = None

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

    def size_set(self, size: int):
        if self.size >= size:
            return
            
        self.size_increase(size - self.size)
        
    def size_increase(self, size: int):
        self.memory += bytearray(size)
        self.size += size
        self.bounds = range(self.size)

    def get(self, offset: int, size: int) -> bytes:
        self.__test_bounds(offset, size, 'Memory.get')

        return self.memory[offset:offset + size]

    def set(self, offset: int, value: bytes) -> None:
        size = len(value)
        self.__test_bounds(offset, size, 'Memory.set')

        self.memory[offset:offset + size] = value

    def fill(self, offset: int, value: int) -> None:
        self.__test_bounds(offset, 1, 'Memory.fill')
        assert value in range(256)

        for i in range(offset, self.bounds.stop):
            self.memory[i] = value
