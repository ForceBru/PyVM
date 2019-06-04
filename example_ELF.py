import VM


def enable_logging(verbose=False, file=None):
    import logging, sys

    FMT_1 = '%(levelname)s: %(module)s.%(funcName)s @ %(lineno)d: %(message)s'
    FMT_2 = '%(message)s'
    logging.basicConfig(
        stream=file or sys.stdout,
        level=logging.DEBUG,
        format=FMT_1 if verbose else FMT_2
    )


if __name__ == '__main__':
    #f = open('io.elf_new_log.txt', 'w')
    #enable_logging()
    mem = 0x0017801d
    vm = VM.VM(mem)  # memory will be allocated automatically

    import time
    s = time.process_time()
    vm.execute_elf(f'C/bin/quicksort.elf')
    vm.execute_elf(f'C/bin/insertionsort.elf')
    vm.execute_elf(f'C/bin/bubblesort.elf')
    e = time.process_time()
    print(f'Sorts: NEW done in {e-s:.3f}')
    
    s = time.process_time()
    vm.execute_elf(f'C/bin/memcpy_test.elf')
    e = time.process_time()
    print(f'Memcpy: NEW done in {e-s:.3f}')
    
    print(f'Speedups compared to OLD: (1.6321214808246507, 1.6896864472661313)')
    #vm.execute_elf(f'C/bin/recursion.elf')
    #vm.execute_elf(f'C/bin/hello_world.elf')
    #vm.execute_elf(f'C/bin/io.elf')
    #vm.execute_elf(f'C/bin/calculator.elf')
    #f.close()
