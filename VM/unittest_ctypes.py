import unittest
import os
import ctypes
import random

from Memory_ctypes import Memory
from Registers_ctypes import Reg32

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
            self.mem.set_val(offset, 1, correct)
            ret = self.mem.get(offset, 1)

            self.assertEqual(ret, correct)

    def do_test_set(self, size: int):
        for offset in range(self.mem.size - size):
            correct = int.from_bytes(os.urandom(size), 'little')
            self.mem.set_val(offset, size, correct)
            ret = self.mem.get(offset, size)

            self.assertEqual(ret, correct)

        for offset in range(1, self.mem.size - size):
            correct = int.from_bytes(os.urandom(size), 'little')
            self.mem.set_val(offset, size, correct)
            ret = self.mem.get(offset, size)

            self.assertEqual(ret, correct)

        if size == 4:
            for offset in range(2, self.mem.size - size):
                correct = int.from_bytes(os.urandom(size), 'little')
                self.mem.set_val(offset, size, correct)
                ret = self.mem.get(offset, size)

                self.assertEqual(ret, correct)

            for offset in range(3, self.mem.size - size):
                correct = int.from_bytes(os.urandom(size), 'little')
                self.mem.set_val(offset, size, correct)
                ret = self.mem.get(offset, size)

                self.assertEqual(ret, correct)

    def test_set_16(self):
        self.do_test_set(2)

    def test_set_32(self):
        self.do_test_set(4)


class TestRegisters(unittest.TestCase):
    NAMES_4 = {
        'eax': 0, 'ecx': 1, 'edx': 2, 'ebx': 3,
        'esp': 4, 'ebp': 5,
        'esi': 6, 'edi': 7
    }
    NAMES_2 = {name[1:]: val for name, val in NAMES_4.items()}

    NAMES_LO = {'al': 0, 'cl': 1, 'dl': 2, 'bl': 3}
    NAMES_HI = {'ah': 4, 'ch': 5, 'dh': 6, 'bh': 7}

    def setUp(self):
        self.reg = Reg32()

        self.random_data = [int.from_bytes(os.urandom(4), 'little') for _ in 'eax ecx edx ebx esp ebp esi edi'.split()]

        self.reg.eax = self.random_data[0]
        self.reg.ecx = self.random_data[1]
        self.reg.edx = self.random_data[2]
        self.reg.ebx = self.random_data[3]
        self.reg.esp = self.random_data[4]
        self.reg.ebp = self.random_data[5]
        self.reg.esi = self.random_data[6]
        self.reg.edi = self.random_data[7]

    def test_get_32(self):
        for name, offset in self.NAMES_4.items():
            correct = self.random_data[offset]
            stored = getattr(self.reg, name)

            with self.subTest(register=(name, offset), correct=correct, stored=stored):
                ret = self.reg.get(offset, 4)

                self.assertEqual(ret, correct)

    def test_get_16(self):
        for name, offset in self.NAMES_2.items():
            correct = self.random_data[offset] & 0xFFFF
            stored = getattr(self.reg, name)

            with self.subTest(register=(name, offset), correct=correct, stored=stored):
                ret = self.reg.get(offset, 2)

                self.assertEqual(ret, correct)

    def test_get_lo(self):
        for name, offset in self.NAMES_LO.items():
            correct = self.random_data[offset] & 0xFF
            stored = getattr(self.reg, name)

            with self.subTest(register=(name, offset), correct=correct, stored=stored):
                ret = self.reg.get(offset, 1)

                self.assertEqual(ret, correct)

    def test_get_hi(self):
        for name, offset in self.NAMES_HI.items():
            correct = (self.random_data[offset % 4] >> 8) & 0xFF
            stored = getattr(self.reg, name)

            with self.subTest(register=(name, offset), correct=correct, stored=stored):
                ret = self.reg.get(offset, 1)

                self.assertEqual(ret, correct)


if __name__ == '__main__':
    unittest.main(verbosity=2)
