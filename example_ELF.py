import VM


def enable_logging(verbose=False):
    import logging, sys

    FMT_1 = '%(levelname)s: %(module)s.%(funcName)s @ %(lineno)d: %(message)s'
    FMT_2 = '%(message)s'
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format=FMT_1 if verbose else FMT_2
    )


if __name__ == '__main__':
    # enable_logging()
    mem = 50_000
    import io
    void = io.StringIO()
    vm = VM.VM(mem, void, void, void)
    
    import time
    s = time.process_time()
    vm.execute_elf(f'C/bin/quicksort.elf')
    vm.execute_elf(f'C/bin/bubblesort.elf')
    vm.execute_elf(f'C/bin/insertionsort.elf')
    vm.execute_elf(f'C/bin/memcpy_test.elf')
    e = time.process_time()
    
    print(f'NEW Done in {e-s:.3f} sec')
    #vm.execute_elf(f'C/bin/args.elf', ('--help', ))
