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

* `add`  (*)
* `and`  (*)
* `call` (*)
* `cmp`  (*)
* `jcc`  (*) (only 8-bit relative addressing supported)
* `jmp`  (*)
* `int`
* `lea`
* `mov`  (*)
* `neg`  (*)
* `not`  (*)
* `or`   (*)
* `pop`  (*)
* `push` (*)
* `ret`  (*)
* `sub`  (*)
* `test` (*)
* `xor`  (*)


## Example

Before running this you may consider setting `debug = False` in `VM/debug.py`.

	import binascii

	import VM

	binary = "B8 04 00 00 00" \
	         "BB 01 00 00 00" \
             "B9 29 00 00 00" \
             "BA 0E 00 00 00" \
             "CD 80" \
             "E9 02 00 00 00" \
             "89 C8" \
             "B8 01 00 00 00" \
             "BB 00 00 00 00" \
             "CD 80" \
             "48 65 6C 6C 6F 2C 20 77 6F 72 6C 64 21 0A".replace(' ', '')

    # convert the hexadecimal representation above to bytes
    binary = binascii.unhexlify(binary)

    # initialize the VM with 1024 bytes of memory
    vm = VM.VM(1024)

    vm.execute_bytes(binary)

    # output:
    # Hello, world!
    # [!] Process exited with code 0

## TODO

* Add segment registers
* Implement more instructions
* Add basic memory protection

## How to contribute

Everyone is welcome to contribute! For some guidelines, please refer to the comments in the project, especilly in `VM/__init__.py`, `VM/fetchLoop.py` and `VM/internals.py`.