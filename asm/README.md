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
│   ├── c_float1.bin
│   ├── c_float2.bin
│   ├── ...
│   └── test_xchg.bin
├── c
│   ├── Makefile
│   ├── loop.c
│   ├── loop.s
│   ├── pointers.c
│   ├── pointers.s
│   ├── pow.c
│   └── pow.s
├── c_float1.s
├── c_float2.s
├── ...
└── test_xchg.s
```

The files in `bin` are compiled using NASM (should be installed separately to compile assembly for x86) from the `.s`
files in the root directory. The actual build process is governed by `PyVM/compile_asm.py` <sub>which could be replaced
by a `Makefile`, but then we'd (almost?) lose the ability to test compilation in `RyVM/test_VM.py`</sub>.

The purpose of files in `c` remains unknown... 