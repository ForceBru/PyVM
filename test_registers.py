import unittest
import os


from VM.Registers import Reg32


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

        self.random_data = [
            int.from_bytes(os.urandom(4), 'little')
            for _ in 'eax ecx edx ebx esp ebp esi edi'.split()
        ]

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

            with self.subTest(register=(name, offset), correct=correct, stored=stored, signed=False):
                ret = self.reg.get(offset, 4)

                self.assertEqual(ret, correct)

            correct = int.from_bytes(correct.to_bytes(4, 'little'), 'little', signed=True)
            with self.subTest(register=(name, offset), correct=correct, stored=stored, signed=True):
                ret = self.reg.get(offset, 4, True)

                self.assertEqual(ret, correct)

    def test_get_16(self):
        for name, offset in self.NAMES_2.items():
            correct = self.random_data[offset] & 0xFFFF
            stored = getattr(self.reg, name)

            with self.subTest(register=(name, offset), correct=correct, stored=stored):
                ret = self.reg.get(offset, 2)

                self.assertEqual(ret, correct)

            correct = int.from_bytes(correct.to_bytes(2, 'little'), 'little', signed=True)
            with self.subTest(register=(name, offset), correct=correct, stored=stored, signed=True):
                ret = self.reg.get(offset, 2, True)

                self.assertEqual(ret, correct)

    def test_get_lo(self):
        for name, offset in self.NAMES_LO.items():
            correct = self.random_data[offset] & 0xFF
            stored = getattr(self.reg, name)

            with self.subTest(register=(name, offset), correct=correct, stored=stored):
                ret = self.reg.get(offset, 1)

                self.assertEqual(ret, correct)

            correct = int.from_bytes(correct.to_bytes(1, 'little'), 'little', signed=True)
            with self.subTest(register=(name, offset), correct=correct, stored=stored, signed=True):
                ret = self.reg.get(offset, 1, True)

                self.assertEqual(ret, correct)

    def test_get_hi(self):
        for name, offset in self.NAMES_HI.items():
            correct = (self.random_data[offset % 4] >> 8) & 0xFF
            stored = getattr(self.reg, name)

            with self.subTest(register=(name, offset), correct=correct, stored=stored):
                ret = self.reg.get(offset, 1)

                self.assertEqual(ret, correct)

            correct = int.from_bytes(correct.to_bytes(1, 'little'), 'little', signed=True)
            with self.subTest(register=(name, offset), correct=correct, stored=stored, signed=True):
                ret = self.reg.get(offset, 1, True)

                self.assertEqual(ret, correct)


if __name__ == '__main__':
    unittest.main(verbosity=2)
