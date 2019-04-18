import unittest
import os
import random

import VM.Memory
import VM.Registers
import VM.CPU

RUNS = 100
MEMSZ = 64 * RUNS


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
            data = os.urandom(self.reg.allowed_sizes[0])[::-1]
            for offset, name in enumerate(self.reg.names):
                self.reg.set(offset, data)
                # print(f"Set {data.hex()} -> {offset:03b}")

                sz = self.reg.allowed_sizes[0]
                with self.subTest(f"'set' method for registers {name}({sz} bytes) failed"):
                    val = self.reg.get(offset, sz)
                    # print(f"\tGot 4 bytes: {val.hex()}, should've gotten: {data.hex()}")
                    self.assertSequenceEqual(val, data)

                sz = self.reg.allowed_sizes[1]
                with self.subTest(f"'set' method for registers {name}({sz} bytes) failed"):
                    val = self.reg.get(offset, sz)
                    # print(f"\tGot 2 bytes: {val.hex()}, should've gotten: {data[:2].hex()}")
                    self.assertSequenceEqual(val, data[:2])

                sz = self.reg.allowed_sizes[2]
                with self.subTest(f"'set' method for registers {name}({sz} bytes) failed"):
                    val = self.reg.get(offset, sz)
                    correct = bytes([data[(offset >> 2) & 1]])
                    # print(f"\tGot 1 byte: {val.hex()}, should've gotten: {correct.hex()}")
                    self.assertSequenceEqual(self.reg.get(offset, self.reg.allowed_sizes[2]), correct)


class TestMemory(unittest.TestCase):
    def setUp(self):
        self.mem = VM.Memory.Memory(MEMSZ)

    def test_emptiness(self):
        for x in range(RUNS):
            size = random.randint(0, MEMSZ // 2)
            offset = random.randint(0, MEMSZ - size)
                

            try:
                self.assertSequenceEqual(self.mem.get(offset, size), bytearray(size))
            except AssertionError:
                ...

    def test_set_data(self):
        for x in range(RUNS):
            size = random.randint(0, MEMSZ // 2)
            offset = random.randint(0, MEMSZ - size)
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
        self.cpu.mem.program_break = MEMSZ
        self.data = [os.urandom(random.choice([1, 2, 4])) for _ in range(RUNS)]

    def test_push_pop(self):
        for x in self.data:
            self.cpu.stack_push(x)

        for i, x in enumerate(reversed(self.data)):
            l = len(x)
            
            with self.subTest("x = '{}' (#{}) failed".format(x, i)):
                popped = self.cpu.stack_pop(self.cpu.operand_size)
                
                if l < self.cpu.operand_size:
                    self.assertTrue(sum(popped[l:]) == 0)
                    popped = popped[:l]
                    
                self.assertSequenceEqual(popped, x)


if __name__ == "__main__":
    unittest.main(verbosity=2)
