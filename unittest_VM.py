import unittest
import VM

MEMSZ = 1024 * 10


class TestRegisters(unittest.TestCase):
    def setUp(self):
        self.vm = VM.VM(MEMSZ)

    def test_jmp_int(self):
        self.vm.execute_file('asm/test_jmp_int.bin')

    def test_push_pop(self):
        self.vm.execute_file('asm/test_push_pop.bin')

    def test_call_ret(self):
        self.vm.execute_file('asm/test_call_ret.bin')

    def test_add_sub(self):
        self.vm.execute_file('asm/test_add_sub.bin')

    def test_lea(self):
        self.vm.execute_file('asm/test_lea.bin')

    def cmp_jcc(self):
        self.vm.execute_file('asm/test_cmp_jcc.bin')

    def test_bitwise(self):
        self.vm.execute_file('asm/test_bitwise.bin')

    def test_test(self):
        self.vm.execute_file('asm/test_test.bin')

    def test_inc_dec(self):
        self.vm.execute_file('asm/test_inc_dec.bin')

    def test__c_pointers(self):
        self.vm.execute_file('asm/c_pointers.bin')  # exit code 1

    def test__c_loop(self):
        self.vm.execute_file('asm/c_loop.bin')  # exit code 10

    #def test__c_pow(self):
    #    self.vm.execute_file('asm/c_pow.bin')

if __name__ == "__main__":
    unittest.main(verbosity=2)