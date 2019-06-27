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
    vm = VM.VMKernel(10_000)

    vm.execute(VM.ExecutionStrategy.ELF, "C/bin/calculator.elf")

if __name__ == '__float_matmul_benchmark__':
    mem = 0x0017801d

    vm = VM.VMKernel(mem)

    import datetime
    s = datetime.datetime.now()
    print('Starting multiplication at', s)
    retcode = vm.execute(VM.ExecutionStrategy.ELF, 'C/bin/float_matmul.elf')
    e = datetime.datetime.now()

    if retcode != 0:
        print('[ERROR] The result of multiplication was not correct! Error code:', retcode)

    print('Multiplication done at', e)
    print('Multiplied in', e - s)

if __name__ == '__run_nasm__':
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
    retval = vm.execute(
        VM.ExecutionStrategy.ELF,  # How to execute?
        'C/real_life/nasm',  # What to execute?
        ('-o', outfile, '-O0', infile)  # What arguments to pass to the executable?
    )
    end = datetime.datetime.now()
    print(f'[{end}] NASM done in {end - start}')

    if retval == 0:
        print(f'Hurray! NASM is done! Now executing the resulting binary...')
        retval = vm.execute(VM.ExecutionStrategy.FLAT, outfile)
        print(f'Compiled file executed with exit code {retval}')
    else:
        print(f'NASM could not compile {infile}. Exit code: {retval}')

if __name__ == '__speed_test__':
    # enable_logging()
    mem = 0x0017801d
    vm = VM.VMKernel(mem)

    TEST_C = 0

    if TEST_C:
        from pathlib import Path

        for name in Path('C/bin').glob('*.elf'):
            name = str(name)
            print(f'Running {name}...')
            mem = 0x0017801d
            vm = VM.VMKernel(mem)
            vm.execute(VM.ExecutionStrategy.ELF, name)
            print(f'Finished running {name}')

    import timeit
    from io import StringIO

    print("Testing...")
    t = timeit.repeat(
        "vm.execute(VM.ExecutionStrategy.ELF, 'C/bin/bubblesort.elf');"
        "vm.execute(VM.ExecutionStrategy.ELF, 'C/bin/quicksort.elf');"
        "vm.execute(VM.ExecutionStrategy.ELF, 'C/bin/insertionsort.elf');"
        "vm.execute(VM.ExecutionStrategy.ELF, 'C/bin/memcpy_test.elf')",
        "void=StringIO();vm=VM.VMKernel(0x0017801d, void, void, void)",
        globals={'VM': VM, 'StringIO': StringIO}, number=10, repeat=10)

    avg = lambda x: sum(x) / len(x)
    print(f"LATEST: {min(t):.4f}, {avg(t):.4f}, {max(t):.4f}")
    # OLD                     : 26.6493, 28.4966, 29.9140
    # NEW (rolled back)       : 28.6566, 29.1709, 29.9998
    # LATEST                  : 23.2240, 25.5855, 27.2388
    # LATEST (ModRM checks)   : 23.2138, 23.7009, 24.1041
    # LATEST (simpler ModRM)  : 20.9989, 21.7070, 22.2221

    # LATEST (no optimization): 23.9340, 24.1104, 24.3951
    # LATEST (optimized)      : 18.4462, 18.9581, 19.3844
