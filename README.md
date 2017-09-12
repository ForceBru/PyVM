# PyVM - execute x86 bytecode in pure Python!

------------------

PyVM is a Python module that allows to execute x86 bytecode on any hardware where Python can run, with no external dependencies.

##Features
	* 32-, 16- and 8-bit registers
	* stack
	* user memory
	* stdin and stdout

##Instructions currently supported

The instructions  marked wth `*` are supported partially. For the actual reasons of this partial support, please see the comments in `VM/__init__.py`.
	* `add` (*)
	* `call` (*)
	* `int`
	* `jmp` (*)
	* `mov` (*)
	* `pop` (*)
	* `push` (*)
	* `ret` (*)

##TODO
	* Add segment registers
	* Implement more instructions
	* Add basic memory protection

##How to contribute
Everyone is welcome to contribute! For some guidelines, please refer to the comments in the project, especilly in `VM/__init__.py`, `VM/fetchLoop.py` and `VM/internals.py`.