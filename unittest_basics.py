import unittest
import os
import random

import VM.Memory
import VM.Registers
import VM.CPU

RUNS = 100
MEMSZ = 64 * RUNS


class TestStack(unittest.TestCase):
    def setUp(self):
        self.cpu = VM.CPU.CPU32(MEMSZ)
        self.cpu.mem.program_break = 0
        self.data = [
            int.from_bytes(os.urandom(4), 'little')
            for _ in range(RUNS)
        ]

    def test_push_pop(self):
        for x in self.data:
            self.cpu.stack_push(x)

        for i, x in enumerate(reversed(self.data)):
            
            with self.subTest("x = '{}' (#{}) failed".format(x, i)):
                popped = self.cpu.stack_pop(self.cpu.operand_size)
                
                self.assertEqual(popped, x)


if __name__ == "__main__":
    unittest.main(verbosity=2)
