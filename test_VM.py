import unittest
import io

from pathlib import Path

from compile_asm import compile_all, find_nasm_executable
import VM

binaries_path = Path('asm/bin')


def can_find_nasm() -> bool:
    try:
        find_nasm_executable()
    except:
        return False
    return True


class TestInserter(type):
    def __new__(mcs, cls_name, parents, scope):
        binaries_in_path = set(p.name.rsplit('.', 1)[0] for p in binaries_path.glob('*.bin'))
        test_names = set(scope['CORRECT'])

        not_tested = binaries_in_path - test_names
        if not_tested:
            print(f'[WARNING] Untested binary files found: {not_tested}')

        nonexistent_files = test_names - binaries_in_path
        if nonexistent_files:
            raise ValueError(f'The following tests exist, but the corresponding files were not found in {binaries_path}: {nonexistent_files}')

        for name in test_names:
            func_name = 'test_' + name
            scope[func_name] = scope['do_test']

        return type(cls_name, parents, scope)


@unittest.skipIf(
    not can_find_nasm(),
    "Skipping assembling because no NASM executable was found"
)
class TestAssemble(unittest.TestCase):
    def test_assemble(self):
        self.assertEqual(compile_all(), 0, 'Failed to assemble binaries!')


def Ret(x):
    return '', x


def Msg(msg):
    return msg, 0


def Both(msg, x):
    return msg, x


class TestInstructions(unittest.TestCase, metaclass=TestInserter):
    MEMSZ = 1024 * 10

    CORRECT = {
        'c_float1': Ret(28),
        'c_float2': Ret(12),
        'c_float3': Ret(0),
        'c_float4': Ret(0),
        'c_float_vecmul': Ret(56),
        'c_loop': Ret(10),
        'c_pointers': Ret(1),
        'c_pow': Ret(625),
        'c_stdlib': Msg('Hello, world!\n'),
        'c_stdlib_O3': Msg('Hello, world!\n'),

        'test_adc': Msg('Testing adc...\nAdding two large numbers...\nSuccess!\n'),
        'test_add_sub': Msg('Testing add and sub...\nOK\nOH\nOK\n'),
        'test_bitwise': Msg(
            'Testing AND...\nTesting OR...\nTesting XOR...\nTesting NOT...\nTesting NEG...\nAll tests succeeded!!\n'),
        'test_call_ret': Msg('Testing call and ret...\nInside the function...\nInside _start again, great!\n'),
        'test_cmp_jcc': Msg('Testing cmp and jcc...\nSuccess!\nSuccess!\nSuccess!\n'),
        'test_div': Msg('Testing div...\n'),
        'test_idiv': Msg('Testing idiv...\n'),
        'test_imul': Msg('Testing imul...\n'),
        'test_imul2': Ret(0),
        'test_inc_dec': Ret(0),
        'test_jmp_int': Msg('Testing unconditional jumps and interrupts...\nSuccess!\n'),
        'test_lea': Msg('Testing lea...\nSuccess!\n'),
        'test_mul': Msg('Testing mul...\nSuccess!\n'),
        # 'test_push_pop':
        'test_registers': Ret(0),
        'test_sbb': Msg('Testing sbb...\nSubtracting two large numbers...\nSuccess!\n'),
        'test_stos': Both('0', 0),
        'test_shifts': Ret(0),
        'test_shr_shl': Msg('Testing shifts...\nSuccess!\n'),
        'test_test': Msg('Testing test...\nSuccess!\n'),
        'test_xchg': Both('Testing xchg...\n', 1000)
    }

    def do_test(self):
        file_name = self._testMethodName[5:]
        correct_msg, correct_retval = self.CORRECT[file_name]

        self.vm.execute(VM.ExecutionStrategy.FLAT, f'asm/bin/{file_name}.bin')

        _stdout = self.stdout.getvalue()

        self.assertSequenceEqual(_stdout, correct_msg)
        self.assertEqual(correct_retval, self.vm.RETCODE)

    def setUp(self):
        self.stdin = io.StringIO()
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()

        self.vm = VM.VMKernel(self.MEMSZ, self.stdin, self.stdout, self.stderr)

    def tearDown(self):
        self.stdin.close()
        self.stdout.close()
        self.stderr.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
