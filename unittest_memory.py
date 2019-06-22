import unittest
import os
import ctypes


from VM.Memory import Memory


class TestMemory(unittest.TestCase):
    MEM_SIZE = 512
    MAX_RANDOM_REPEAT = 10_000

    def setUp(self):
        self.mem = Memory(self.MEM_SIZE)
        self.random_data = os.urandom(self.MEM_SIZE)
        ctypes.memmove(self.mem.mem, self.random_data, self.MEM_SIZE)

    def test_1_size(self):
        self.assertEqual(self.mem.size, self.MEM_SIZE)

    def test_get_8(self):
        for offset in range(self.mem.size):
            ret = self.mem.get(offset, 1)
            correct = self.random_data[offset]

            self.assertEqual(ret, correct)

    def do_test_get(self, size: int):
        for offset in range(self.mem.size - size):
            ret = self.mem.get(offset, size)
            correct = int.from_bytes(self.random_data[offset:offset + size], 'little')

            self.assertEqual(ret, correct)

        for offset in range(1, self.mem.size - size):
            ret = self.mem.get(offset, size)
            correct = int.from_bytes(self.random_data[offset:offset + size], 'little')

            self.assertEqual(ret, correct)

        if size == 4:
            # test all possible permutations
            for offset in range(2, self.mem.size - size):
                ret = self.mem.get(offset, size)
                correct = int.from_bytes(self.random_data[offset:offset + size], 'little')

                self.assertEqual(ret, correct)

            for offset in range(3, self.mem.size - size):
                ret = self.mem.get(offset, size)
                correct = int.from_bytes(self.random_data[offset:offset + size], 'little')

                self.assertEqual(ret, correct)

    def test_get_16(self):
        self.do_test_get(2)

    def test_get_32(self):
        self.do_test_get(4)

    def test_set_8(self):
        for offset in range(self.mem.size):
            correct, = os.urandom(1)
            self.mem.set(offset, 1, correct)
            ret = self.mem.get(offset, 1)

            self.assertEqual(ret, correct)

    def do_test_set(self, size: int):
        for offset in range(self.mem.size - size):
            correct = int.from_bytes(os.urandom(size), 'little')
            self.mem.set(offset, size, correct)
            ret = self.mem.get(offset, size)

            self.assertEqual(ret, correct)

        for offset in range(1, self.mem.size - size):
            correct = int.from_bytes(os.urandom(size), 'little')
            self.mem.set(offset, size, correct)
            ret = self.mem.get(offset, size)

            self.assertEqual(ret, correct)

        if size == 4:
            for offset in range(2, self.mem.size - size):
                correct = int.from_bytes(os.urandom(size), 'little')
                self.mem.set(offset, size, correct)
                ret = self.mem.get(offset, size)

                self.assertEqual(ret, correct)

            for offset in range(3, self.mem.size - size):
                correct = int.from_bytes(os.urandom(size), 'little')
                self.mem.set(offset, size, correct)
                ret = self.mem.get(offset, size)

                self.assertEqual(ret, correct)

    def test_set_16(self):
        self.do_test_set(2)

    def test_set_32(self):
        self.do_test_set(4)


if __name__ == '__main__':
    unittest.main(verbosity=2)
