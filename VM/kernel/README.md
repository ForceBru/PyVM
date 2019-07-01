# PyVM - execute x86 bytecode in pure Python!

[![Build Status](https://travis-ci.org/ForceBru/PyVM.svg?branch=master)](https://travis-ci.org/ForceBru/PyVM)

PyVM executes x86 (IA-32) bytecode in _pure Python_, without any dependencies.

------

This is where the system calls are implemented.

Each syscall must be registered first. Also, its implementation should be _fully annotated_.

Example implementation:

```python
# Put this in, say, `kernel_test.py`

from .kernel import Kernel, Uint, Int


@Kernel.register(0x00)  # Imaginary syscall number
def sys_weird(kernel: Kernel, first_arg: Uint, second_arg: Int) -> int:
    string_address = 0  # Just a random address
    data = b'Hello'
    kernel.cpu.mem.set_bytes(string_address, len(data), data)  # Write to memory
    
    kernel.sys_write(
        1,  # SYS_STDOUT
        string_address,
        len(data)
    )  # Call existing syscall
    
    return first_arg + second_arg  # This will be stored in `cpu.reg.eax`

```