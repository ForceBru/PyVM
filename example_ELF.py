import VM

import logging, sys
FMT_1 = '%(levelname)s: %(module)s.%(funcName)s @ %(lineno)d: %(message)s'
FMT_2 = '%(message)s'
#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=FMT_2)

hello_world = 'hello_world'
hello = 'hello'
helloc = 'helloc'
helloc_native = 'helloc_native'
hello_dyn = 'hello_dynamic'
bash  = 'elf-Linux-x86-bash'


if __name__ == '__main__':
    mem = 344860000
    vm = VM.VM(mem)  # memory will be allocated automatically

    vm.execute_elf(f'VM/ELF/samples/{helloc_native}')

