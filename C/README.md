# PyVM - execute x86 bytecode in pure Python!

[![Build Status](https://travis-ci.org/ForceBru/PyVM.svg?branch=master)](https://travis-ci.org/ForceBru/PyVM)

PyVM executes x86 (IA-32) bytecode in _pure Python_, without any dependencies.

------

This directory contains some sample executables that can be run on _any operating system_ where Python runs via PyVM.

Directory structure:
```text
.
├── Makefile
├── README.md
├── bin
│   ├── args.elf
│   ├── bubblesort.elf
│   ├── ...
│   └── uname.elf
├── real_life
│   ├── nasm
│   ├── nasm_compiled.bin
│   ├── ndisasm
│   └── tcc
└── src
    ├── args.c
    ├── bubblesort.c
    ├── ...
    └── uname.c
```

Each source file `src/%1.c` has a corresponding executable in `bin/%1.elf` that was produced via the `Makefile`.
To build a new executable simply add a new `.c` file to `src` and run `make` from the current directory (`PyVM/C`).