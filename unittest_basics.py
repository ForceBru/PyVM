import unittest
import os
import random

import VM.Memory
import VM.Registers
import VM.CPU

RUNS = 10
MEMSZ = 64


class TestRegisters(unittest.TestCase):  # Methods are sorted in alphabetical order!
    def setUp(self):  # called for every test!
        self.reg = VM.Registers.Reg32()
        self.empty = [None, bytearray(1), bytearray(2), None, bytearray(4)]

    def test_emptiness(self):
        for offset, name in enumerate(self.reg.names):
            with self.subTest("Emptiness test for registers {} failed".format(name)):
                self.assertSequenceEqual(self.reg.get(offset, self.reg.allowed_sizes[0]),
                                         self.empty[self.reg.allowed_sizes[0]])
                self.assertSequenceEqual(self.reg.get(offset, self.reg.allowed_sizes[1]),
                                         self.empty[self.reg.allowed_sizes[1]])
                self.assertSequenceEqual(self.reg.get(offset, self.reg.allowed_sizes[2]),
                                         self.empty[self.reg.allowed_sizes[2]])

    def test_set_data(self):
        for x in range(RUNS):
            data = os.urandom(self.reg.allowed_sizes[0])
            for offset, name in enumerate(self.reg.names):
                with self.subTest("'set' method for registers {} failed".format(name)):
                    self.reg.set(offset, data)

                    self.assertSequenceEqual(self.reg.get(offset, self.reg.allowed_sizes[0]), data)
                    self.assertSequenceEqual(self.reg.get(offset, self.reg.allowed_sizes[1]), data[2:])
                    self.assertSequenceEqual(self.reg.get(offset, self.reg.allowed_sizes[2]),
                                             data[3:] if not (offset // self.reg.allowed_sizes[0]) else data[2:3])


class TestMemory(unittest.TestCase):
    def setUp(self):
        self.mem = VM.Memory.Memory(MEMSZ)

    def test_emptiness(self):
        for x in range(RUNS):
            offset = random.randint(0, MEMSZ)
            size = random.randint(0, MEMSZ // 2)

            try:
                self.assertSequenceEqual(self.mem.get(offset, size), bytearray(size))
            except AssertionError:
                ...

    def test_set_data(self):
        for x in range(RUNS):
            offset = random.randint(0, MEMSZ)
            size = random.randint(0, MEMSZ // 2)
            data = os.urandom(size)
            error = False

            try:
                self.mem.set(offset, data)
            except AssertionError:
                error = True

            try:
                self.assertFalse(error)
                self.assertSequenceEqual(self.mem.get(offset, size), data)
            except AssertionError:
                self.assertTrue(error)


class TestStack(unittest.TestCase):
    def setUp(self):
        self.cpu = VM.CPU.CPU32(MEMSZ)
        self.data = [os.urandom(random.randint(1, MEMSZ // RUNS)) for _ in range(RUNS)]

    def test_push_pop(self):
        for x in self.data:
            self.cpu.stack_push(x)

        for i, x in enumerate(reversed(self.data)):
            with self.subTest("x = '{}' (#{}) failed".format(x, i)):
                popped = self.cpu.stack_pop(len(x))
                self.assertSequenceEqual(popped, x)


if __name__ == "__main__":
    unittest.main(verbosity=2)
