import VM

hello_world = 'hello_world'
hello = 'hello'
hello_dyn = 'hello_dynamic'
bash  = 'elf-Linux-x86-bash'


if __name__ == '__main__':
    vm = VM.VM(64)  # memory will be allocated automatically

    vm.execute_elf(f'VM/ELF/samples/{hello_dyn}')

