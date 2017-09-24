class Memory:
    def __init__(self, size: int):
        self.memory = bytearray(size)
        self.bounds = range(size)
        self.size = size

    def get(self, offset: int, size: int) -> bytes:
        assert offset in self.bounds
        assert offset + size in self.bounds

        return self.memory[offset:offset + size]

    def set(self, offset: int, value: bytes) -> None:
        size = len(value)
        assert offset in self.bounds
        assert offset + size in self.bounds

        self.memory[offset:offset + size] = value

    def fill(self, offset: int, value: int) -> None:
        assert offset in self.bounds
        assert value in range(256)

        for i in range(offset, self.bounds.stop):
            self.memory[i] = value
