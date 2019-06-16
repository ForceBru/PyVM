import logging
import VM


def enable_logging(verbose=False, file=None, level=logging.DEBUG):
    import sys

    FMT_1 = '%(levelname)s: %(module)s.%(funcName)s @ %(lineno)d: %(message)s'
    FMT_2 = '%(message)s'
    logging.basicConfig(
        stream=file or sys.stdout,
        level=level,
        format=FMT_1 if verbose else FMT_2
    )

if __name__ == '__main__':
    enable_logging(level=logging.DEBUG)
    mem = 0x0017801d

    vm = VM.VMKernel(mem)
    vm.execute(VM.ExecutionStrategy.ELF, 'C/bin/float_matmul.elf')

if __name__ == '__mai__':
    # enable_logging(level=logging.INFO)
    # enable_logging(level=logging.DEBUG)
    mem = 0x0017801d * 5

    import os, datetime

    infile = 'asm/standalone.s'
    outfile = 'C/real_life/nasm_compiled.bin'

    try:
        os.unlink(outfile)
    except:
        ...

    vm = VM.VMKernel(mem)

    start = datetime.datetime.now()
    print(f'[{start}] nasm -o {outfile} -O0 {infile}\nPLEASE WAIT! This is going to be VERY slow.\nSeriously, JUST WAIT.')
    retval = vm.execute(VM.ExecutionStrategy.ELF, 'C/real_life/nasm', ('-o', outfile, '-O0', infile, ))
    end = datetime.datetime.now()
    print(f'[{end}] NASM done in {end - start}')

    if retval == 0:
        print(f'Hurray! NASM is done! Now executing the resulting binary...')
        retval = vm.execute(VM.ExecutionStrategy.FLAT, outfile)
        print(f'Compiled file executed with exit code {retval}')
    else:
        print(f'NASM could not compile {infile}. Exit code: {retval}')

if __name__ == '__test__':
    # enable_logging()
    mem = 0x0017801d
    vm = VM.VM(mem)

    TEST_C = 1

    if TEST_C:
        from pathlib import Path

        for name in Path('C/bin').glob('*.elf'):
            name = str(name)
            print(f'Running {name}...')
            mem = 0x0017801d
            vm = VM.VM(mem)
            vm.execute_elf(name)
            print(f'Finished running {name}')

    import timeit
    from io import StringIO

    print("Testing...")
    t = timeit.repeat(
        "vm.execute_elf('C/bin/bubblesort.elf');vm.execute_elf('C/bin/quicksort.elf');vm.execute_elf('C/bin/insertionsort.elf');vm.execute_elf('C/bin/memcpy_test.elf')",
        "void=StringIO();vm=VM(0x0017801d, void, void, void)",
        globals={'VM': VM.VM, 'StringIO': StringIO}, number=10, repeat=10)

    avg = lambda x: sum(x) / len(x)
    print(f"LATEST: {min(t):.4f}, {avg(t):.4f}, {max(t):.4f}")
    # OLD                  : 26.6493, 28.4966, 29.9140
    # NEW (rolled back)    : 28.6566, 29.1709, 29.9998
    # LATEST               : 23.2240, 25.5855, 27.2388
    # LATEST (ModRM checks): 23.2138, 23.7009, 24.1041
