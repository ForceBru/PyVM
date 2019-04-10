import VM

hello_world = 'hello_world'
hello = 'hello'
bash  = 'elf-Linux-x86-bash'

vm = VM.VM(64)  # memory will be allocated automatically

vm.execute_elf(f'VM/ELF/samples/hello')

