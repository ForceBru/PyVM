import VM

hello_world = 'hello_world'
hello = 'hello'
helloc = 'helloc'
hello_dyn = 'hello_dynamic'
bash  = 'elf-Linux-x86-bash'


if __name__ == '__main__':
    vm = VM.VM(50_000)  # memory will be allocated automatically

    vm.execute_elf(f'VM/ELF/samples/{helloc}')

