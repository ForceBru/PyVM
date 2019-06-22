# PyVM - execute x86 bytecode in pure Python!

PyVM executes x86 (IA-32) bytecode in _pure Python_, without any dependencies.

It can run multiple types of executables:
 - Raw bytecode (interprets `bytes` and `bytearray`s as bytecode)
 - Flat binaries (for example, those produced by default by NASM; interprets a file's contents as bytecode)
 - ELF binaries (any statically linked ELF binary)
 
Features:
 - x86 CPU (files: `VM/Registers.py`, `VM/CPU.py`, `VM/fetchLoop.py`, `VM/misc.py`)
   - General-purpose registers: 32-bit, 16-bit, 8-bit. See file #1;
   - Segment registers: ES, CS, SS, DS, FS, GS. See file #1;
   - `EFLAGS` register. See file #1;
   - Stack. See file #2;
   - The "fetch-decode-execute" cycle (instruction cycle). Includes prefixes handling. See file #3;
   - ModRM and SIB bytes parser. See file #4 <sub>...which should be refactored</sub>;
 - x87 FPU (files: `VM/FPU.py`)
   - The extended precision floating-point type, a.k.a. `binary80`;
   - 8 data registers: ST(0), ST(1), ..., ST(7);
   - `control`, `status` and `flag` registers;
 - RAM (files: `VM/Memory.py`)
   - Allows to read 8-bit, 16-bit and 32-bit integers, 80-bit, 64-bit and 32-bit floating-point numbers
   and raw bytes at any valid address;
   - Provides basic bounds checking (so that Python doesn't segfault when a program tries to access an invalid address);
   - Provides basic segmented access via segment registers;
 - x86 instruction set (files: `VM/instructions/*`)
   - Bitwise operations: `and`, `or`, `xor`, `test`, `neg`, `not`, `sal`, `sar`, `shl`, `shr`, `shld`, `shrd`;
   - Control flow operations: `nop`, `jmp`, `jcc`, `setcc`, `cmovcc`, `bt`, `int`, `call`, `ret`, `enter`, `leave`, `cpuid`;
   - Floating-point operations: `fld`, `fst`, `fstp`, `fist`, `fistp`, `fmul`, `fmulp`, `fimul`, `faddp`, `fdiv`, `fdivp`,
   `fucom`, `fucomp`, `fucompp`, `fcomi`, `fcomip`, `fucomip`, `fucomipp`, `fldcw`, `fstcw`, `fnstcw`, `fxch`;
   - Integer arithmetic operations: `add`, `sub`, `cmp`, `adc`, `sbb`, `inc`, `dec`, `mul`, `imul`, `div`, `idiv`;
   - Memory management operations: `mov`, `movs`, `movsx`, `movsxd`, `movzx`, `push`, `pop`, `lea`, `xchg`, `cmpxchg`,
   `cbw`, `cwde`, `cwd`, `cdq`, `cmc`, `clc`, `cld`, `stc`, `std`, `bsf`, `bsr`;
   - Repeatable operations: `stos`.
 - Linux system calls (files: `VM/kernel.py`)
   - Input-output: `sys_read`, `sys_write`, `sys_writev`, `sys_open`, `sys_close`, `sys_unlink`, `sys_readlink`;
   - System management: `sys_exit`, `sys_clock_gettime`;
   - Memory management: `brk`, `sys_set_thread_area`, `mmap`, `munmap` <sub>(be warned: the latter two are super buggy)</sub>
   - Some syscalls that are provided by Python's `os` module.
 - Debugger that prints the instructions and syscalls that are being executed in a (relatively) human-readable format.
 
## How to use
Simple example:

```python
import VM  # import the module

def parse_code(code: str) -> bytearray:
    # This just converts the prettified code below to the raw, ugly bytecode. You can ignore this function.
    import re
    
    binary = ''
    regex = re.compile(r"[0-9a-f]+:\s+([^;]+)\s*;.*", re.DOTALL)

    for line in code.strip().splitlines(keepends=False):
        if line.startswith(';'):
            continue
        match = regex.match(line)
        if not match:
            raise ValueError("Malformed code!")
        binary += match.groups()[0]

    return bytearray.fromhex(binary)


if __name__ == "__main__":
    # This is the bytecode we'll run
    code = """
;                           section .text
;                           _start:
0:  b8 04 00 00 00          ;mov    eax,0x4   ; SYS_WRITE
5:  bb 01 00 00 00          ;mov    ebx,0x1   ; STDOUT
a:  b9 29 00 00 00          ;mov    ecx,0x29  ; address of the message
f:  ba 0e 00 00 00          ;mov    edx,0xe   ; length of the message
14: cd 80                   ;int    0x80      ; interrupt kernel
16: e9 02 00 00 00          ;jmp    0x1d      ; _exit
1b: 89 c8                   ;mov    eax,ecx   ; this is here to mess things up if JMP doesn't work
;                           _exit:
1d: b8 01 00 00 00          ;mov    eax,0x1   ; SYS_EXIT
22: bb 00 00 00 00          ;mov    ebx,0x0   ; EXIT_SUCCESS
27: cd 80                   ;int    0x80      ; interrupt kernel
; section .data
29: 48 65 6C 6C 6F 2C 20 77 6F 72 6C 64 21 0A ; "Hello, world!",10
             """

    vm = VM.VMKernel(500)  # Initialize the VM with the Linux kernel and give it 500 bytes of memory.

    # EXECUTE IT!
    vm.execute(
        VM.ExecutionStrategy.BYTES,  # We're executing raw bytecode
        parse_code(code)  # This is the actual bytecode
    )
```

Output:

```
Hello, world!
[!] Process exited with code 0
```

Please see `example_BYTES.py`, `example_FLAT.py` and `example_ELF.py` for more examples of usage.
 
## What this is
 - A toy emulator of the x86 CPU that actually works;
 - A small toy Linux Kernel written in Python that kinda works, but is mostly a giant stub;
 - A learning resource that shows how an Intel CPU may work;
   - The instructions and the basic architecture are implemented according to
   the [Intel Software Developer Manual](https://software.intel.com/en-us/articles/intel-sdm),
   but the algorithms for parsing opcodes, finding the appropriate instruction implementation for an opcode,
   parsing the ModRM and SIB bytes, accessing registers and memory are custom, because they aren't exactly specified
   in the Manual;
   - The implementation of instructions may be buggy, so take the code with a grain of salt.
 - A learning resource that shows how a teeny-tiny <sub>and buggy</sub> replica of the Linux kernel may work;
   - Individual implementations of system calls should have links to the docs that explain how a given syscall works;
   - Some of the syscalls were roughly translated from the C code of the Linux kernel.
   
## What this is not
 - A fast emulator. It's actually super slow. I mean, this is _pure Python_, what did you expect?!
   - Although version `0.1-beta` is almost two times faster than the commit `453fb47617f269fd8fa4ebe7c8cb28cc0611ede0` on master.
 - A fast (or properly implemented, or safe) Linux kernel.
   - At this point (version `0.1-beta`) it's a huge stub that has a minimal set of syscalls that allow basic programs to work.
 - Something that's written by an expert in either CPUs or kernels. There are lots of `TODO`s and bugs.
   - If your program crashes, chances are that this is _not_ you, but it's still possible to get a legitimate segmentation fault.
   Please open an issue about the crash.
   
   
## Found a bug? Have an idea?
You're welcome to contribute! Open issues, pull requests, contact me via Twitter or Reddit.
Learn more about the x86 architecture and the Linux kernel and have fun!