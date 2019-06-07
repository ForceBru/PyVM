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
    # enable_logging()
    mem = 0x0017801d
    import timeit
    from io import StringIO

    print("Testing...")
    t = timeit.repeat(
        "vm.execute_elf('C/bin/bubblesort.elf');vm.execute_elf('C/bin/quicksort.elf');vm.execute_elf('C/bin/insertionsort.elf');vm.execute_elf('C/bin/memcpy_test.elf')",
        "void=StringIO();vm=VM(0x0017801d, void, void, void)",
        globals={'VM': VM.VM, 'StringIO': StringIO}, number=10, repeat=10)

    avg = lambda x: sum(x) / len(x)
    print(f"LATEST: {min(t):.4f}, {avg(t):.4f}, {max(t):.4f}")
    # OLD: 26.6493, 28.4966, 29.9140
    # NEW (rolled back): 28.6566, 29.1709, 29.9998
    # LATEST: 23.2240, 25.5855, 27.2388
