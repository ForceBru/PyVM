# How to contribute

Everyone is welcome to contribute! Here are some guidelines.

## You found a bug

Please open an issue, describe the problem and include the traceback and a minimal, complete and verifiable example that reproduces the error.

## You implemented a new instruction

Awesome! Please try to structure your code in the following way:

### Implementing the instruction

The instructions should be implemented solely in `VM/instructions.py`. If your instruction only has one possible signature (like `ret`, `mul` or `div` and unlike `imul`), it should be implemented as a function, whose first argument should be `self`. Otherwise, it should be a class organized in the following way:

    class MNEMONIC:
        @staticmethod
        def r(vm, ...):
            # do stuff
            
        @staticmethod
        def r_rm(vm, ...):
            # do other stuff
            
            
So that each member function is marked as `@staticmethod`, and its name represents the arguments of the instruction, separated by underscores (`_`). The first argument is the `self` of a `VM` instance.

Each instruction (a fuunction or a class) shall occur after a header in the following form:

    ####################
    # MNEMONIC1 [/ MNEMONIC_I]*
    ####################
    
If you think you can implement multiple instructions as one function or class, it's OK, but please name it accordingly, like `ADDSUB` or `cbwcwde`, for example.

### Adding the instruction to the CPU

The instructions' implementations are to be imported right inside the class' definition, in `VM/__init__.py`. Then, in `VM.__init__`, right before the definition of `self.instr`, introduce a new variable in the following way:

    self._mnemonic = {
        opcode_1: P(self.function_implementation, arg_1=val_1, ...),
        opcode_2: P(self.function_implementation, arg_1=val_2, ...),
    }
    
If the instruction is implemented as a class, use `self.CLASS_IMPLEMENTATION.arg1_arg2` instead of `self.function_implementation`.

### Adding the instruction mnemonic to README.md

This is simple: just add the instruction mnemonic to README.md in alphabetical order.
