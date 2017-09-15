# PyVM - execute x86 bytecode in pure Python!

------------------

PyVM is a Python module that allows to execute x86 32-bit bytecode on any hardware where Python can run, with no external dependencies.

## Features

* 32-, 16- and 8-bit registers
* stack
* user memory
* stdin, stdout and stderr

## Instructions currently supported

The instructions  marked wth `*` are supported partially. For the actual reasons of this partial support, please see the comments in `VM/__init__.py`.

* `add` (*)
* `sub` (*)
* `call` (*)
* `int`
* `jmp` (*)
* `mov` (*)
* `pop` (*)
* `push` (*)
* `ret` (*)

## Example

Before running this you may consider setting `debug = False` in `VM/debug.py`.

	import binascii

	import VM

	binary = "B8 04 00 00 00" \
             "BB 01 00 00 00" \
             "B9 29 00 00 00" \
             "BA 0D 00 00 00" \
             "CD 80" \
             "E9 02 00 00 00" \
             "89 C8" \
             "B8 01 00 00 00" \
             "BB 00 00 00 00" \
             "CD 80" \
             "48 65 6C 6C 6F 2C 20 77 6F 72 6C 64 21 ".replace(' ', '')

    binary = binascii.unhexlify(binary)

    vm = VM.VM(1024)

    vm.mem.set(0, binary)
    vm.run()  # output: Hello, world!

## TODO

* Add segment registers
* Implement more instructions
* Add basic memory protection

## How to contribute

Everyone is welcome to contribute! For some guidelines, please refer to the comments in the project, especilly in `VM/__init__.py`, `VM/fetchLoop.py` and `VM/internals.py`.