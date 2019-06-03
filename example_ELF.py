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
    enable_logging()
    mem = 1024
    vm = VM.VM(mem)  # memory will be allocated automatically

    vm.execute_file('asm/bin/test_imul2.bin')

    # vm.execute_elf(f'C/bin/calculator.elf')  # doesn't work yet
    # vm.execute_elf(f'C/bin/io.elf')
