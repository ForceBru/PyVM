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
    #enable_logging()
    mem = 0x0017801d
    vm = VM.VM(mem)  # memory will be allocated automatically

    #vm.execute_elf(f'C/bin/recursion.elf')
    #vm.execute_elf(f'C/bin/hello_world.elf')
    #vm.execute_elf(f'C/bin/io.elf')
    #vm.execute_elf('C/bin/args.elf', ('--hey', 'test', 'argument'))
    vm.execute_elf('C/bin/reverse_polish.elf')
