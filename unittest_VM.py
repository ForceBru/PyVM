import unittest
import io
import sys

import VM


class TestInstructions(unittest.TestCase):
    MEMSZ = 1024 * 10
    EXIT_SUCCESS = 0
    MSG_EXIT = '[!] Process exited with code {}\n'
    FPATH = 'asm/bin/{}.bin'
    
    def setUp(self):
        self.stdin  = io.StringIO()
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        
        self.vm = VM.VM(self.MEMSZ, self.stdin, self.stdout, self.stderr)
        
    def tearDown(self):
        self.stdin.close()
        self.stdout.close()
        self.stderr.close()

    def check_output(self, stdout, stderr):
        stdout_ = self.stdout.getvalue()
        stderr_ = self.stderr.getvalue()
        
        self.assertSequenceEqual(stdout_, stdout)
        self.assertSequenceEqual(stderr_, stderr)

    def test_jmp_int(self):
        fname = sys._getframe().f_code.co_name
        self.vm.execute_file(self.FPATH.format(fname))
        
        self.check_output(
            'Testing unconditional jumps and interrupts...\nSuccess!\n',
            self.MSG_EXIT.format(self.EXIT_SUCCESS)
            )

    def test_push_pop(self):
        fname = sys._getframe().f_code.co_name
        self.vm.execute_file(self.FPATH.format(fname))
        
        self.check_output(
            'Testing push and pop...\n01\n',
            self.MSG_EXIT.format(self.EXIT_SUCCESS)
            )

    def test_call_ret(self):
        fname = sys._getframe().f_code.co_name
        self.vm.execute_file(self.FPATH.format(fname))
        
        self.check_output(
            'Testing call and ret...\nInside the function...\nInside _start again, great!\n',
            self.MSG_EXIT.format(self.EXIT_SUCCESS)
            )

    def test_add_sub(self):
        fname = sys._getframe().f_code.co_name
        self.vm.execute_file(self.FPATH.format(fname))
        
        self.check_output(
            'Testing add and sub...\nOK\nOH\nOK\n',
            self.MSG_EXIT.format(self.EXIT_SUCCESS)
            )

    def test_adc(self):
        fname = sys._getframe().f_code.co_name
        self.vm.execute_file(self.FPATH.format(fname))

        self.check_output(
            'Testing adc...\nAdding two large numbers...\nSuccess!\n',
            self.MSG_EXIT.format(self.EXIT_SUCCESS)
            )

    def test_sbb(self):
        fname = sys._getframe().f_code.co_name
        self.vm.execute_file(self.FPATH.format(fname))

        self.check_output(
            'Testing sbb...\nSubtracting two large numbers...\nSuccess!\n',
            self.MSG_EXIT.format(self.EXIT_SUCCESS)
            )

    def test_lea(self):
        fname = sys._getframe().f_code.co_name
        self.vm.execute_file(self.FPATH.format(fname))
        
        self.check_output(
            'Testing lea...\nSuccess!\n',
            self.MSG_EXIT.format(self.EXIT_SUCCESS)
            )

    def test_cmp_jcc(self):
        fname = sys._getframe().f_code.co_name
        self.vm.execute_file(self.FPATH.format(fname))
        
        self.check_output(
            'Testing cmp and jcc...\nSuccess!\nSuccess!\nSuccess!\n',
            self.MSG_EXIT.format(self.EXIT_SUCCESS)
            )

    def test_bitwise(self):
        fname = sys._getframe().f_code.co_name
        self.vm.execute_file(self.FPATH.format(fname))
        
        self.check_output(
            'Testing AND...\nTesting OR...\nTesting XOR...\nTesting NOT...\nTesting NEG...\nAll tests succeeded!!\n',
            self.MSG_EXIT.format(self.EXIT_SUCCESS)
            )

    def test_test(self):
        fname = sys._getframe().f_code.co_name
        self.vm.execute_file(self.FPATH.format(fname))
        
        self.check_output(
            'Testing test...\nSuccess!\n',
            self.MSG_EXIT.format(self.EXIT_SUCCESS)
            )

    def test_inc_dec(self):
        fname = sys._getframe().f_code.co_name
        self.vm.execute_file(self.FPATH.format(fname))
        
        self.check_output(
            '',
            self.MSG_EXIT.format(self.EXIT_SUCCESS)
            )
            
    def test_shr_shl(self):
        fname = sys._getframe().f_code.co_name
        self.vm.execute_file(self.FPATH.format(fname))
        
        self.check_output(
            'Testing shifts...\nSuccess!\n',
            self.MSG_EXIT.format(self.EXIT_SUCCESS)
            )

    def test_xchg(self):
        fname = sys._getframe().f_code.co_name
        self.vm.execute_file(self.FPATH.format(fname))

        self.check_output(
            'Testing xchg...\n',
            self.MSG_EXIT.format(1000)
            )

    def test_mul(self):
        fname = sys._getframe().f_code.co_name
        self.vm.execute_file(self.FPATH.format(fname))

        self.check_output(
            'Testing mul...\nSuccess!\n',
            self.MSG_EXIT.format(self.EXIT_SUCCESS)
            )

    def test_div(self):
        fname = sys._getframe().f_code.co_name
        self.vm.execute_file(self.FPATH.format(fname))

        self.check_output(
            'Testing div...\n',
            self.MSG_EXIT.format(self.EXIT_SUCCESS)
            )

    def test_imul(self):
        fname = sys._getframe().f_code.co_name
        self.vm.execute_file(self.FPATH.format(fname))

        self.check_output(
            'Testing imul...\n',
            self.MSG_EXIT.format(self.EXIT_SUCCESS)
            )

    def test_idiv(self):
        fname = sys._getframe().f_code.co_name
        self.vm.execute_file(self.FPATH.format(fname))

        self.check_output(
            'Testing idiv...\n',
            self.MSG_EXIT.format(self.EXIT_SUCCESS)
            )

    def test__c_pointers(self):
        fname = sys._getframe().f_code.co_name.split('__')[1]
        self.vm.execute_file(self.FPATH.format(fname))
        
        self.check_output(
            '',
            self.MSG_EXIT.format(1)
            )

    def test__c_loop(self):
        fname = sys._getframe().f_code.co_name.split('__')[1]
        self.vm.execute_file(self.FPATH.format(fname))
        
        self.check_output(
            '',
            self.MSG_EXIT.format(10)
            )

    def test__c_pow(self):
        fname = sys._getframe().f_code.co_name.split('__')[1]
        self.vm.execute_file(self.FPATH.format(fname))

        self.check_output(
            '',
            self.MSG_EXIT.format(625)
            )


if __name__ == "__main__":
    unittest.main(verbosity=2, failfast=True)
