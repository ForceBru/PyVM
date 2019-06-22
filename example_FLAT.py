import VM

if __name__ == '__main__':
    vm = VM.VMKernel(10_000)

    vm.execute(VM.ExecutionStrategy.FLAT, 'asm/bin/c_stdlib_O3.bin')