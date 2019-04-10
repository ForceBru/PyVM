class Memory:
    def __init__(self, size: int):
        self.memory = bytearray(size)
        self.bounds = range(size)
        self.size = size
        
    def size_set(self, size: int):
        if self.size >= size:
            return
            
        self.size_increase(size - self.size)
        
    def size_increase(self, size: int):
        self.memory += bytearray(size)
        self.size += size
        self.bounds = range(self.size)

    def get(self, offset: int, size: int) -> bytes:
        assert offset in self.bounds, 'Memory.get: offset ({}) not in bounds ({})'.format(offset, self.bounds)
        assert offset + size in self.bounds, 'Memory.get: offset + size ({}) not in bounds ({})'.format(offset + size, self.bounds)

        return self.memory[offset:offset + size]

    def set(self, offset: int, value: bytes) -> None:
        size = len(value)
        assert offset in self.bounds, 'Memory.set: offset ({}) not in bounds ({})'.format(offset, self.bounds)
        assert offset + size in self.bounds, 'Memory.set: offset + size ({}) not in bounds ({})'.format(offset + size, self.bounds)

        self.memory[offset:offset + size] = value

    def fill(self, offset: int, value: int) -> None:
        assert offset in self.bounds
        assert value in range(256)

        for i in range(offset, self.bounds.stop):
            self.memory[i] = value
