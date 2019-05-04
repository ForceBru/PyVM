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


hello_world = 'hello_world'
hello = 'hello'
helloc = 'helloc'
helloc_native = 'helloc_native'
helloc_native_musl = 'helloc_native_musl'
hello_dyn = 'hello_dynamic'
bash  = 'elf-Linux-x86-bash'


if __name__ == '__main__':
    mem = 50_000  # 344_860_000
    vm = VM.VM(mem)  # memory will be allocated automatically

    vm.execute_elf(f'VM/ELF/samples/{helloc_native_musl}')

