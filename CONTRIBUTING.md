# How to contribute

Everyone is welcome to contribute! Here are some guidelines.

## You found a bug

Please open an issue, describe the problem and include the traceback and a minimal, complete and verifiable example that reproduces the error.

## You implemented a new instruction

Awesome! Please try to structure your code in the following way:

### Implementing the instruction

The instructions should be implemented solely in `VM/instructions/<category>.py`. An instruction should be a class organized in the following way:

    # from ..util import Instruction

    class MNEMONIC(Instruction):
        def __init__(self): # this method MUST be here, and it MUST define the following attribute
            self.opcodes = {
                0x00: self.r, # just an example
                0x01: self.rm
                }

        def r(vm, ...):
            ... # do stuff

        def r_rm(vm, ...):
            ... # do other stuff
            
            
Here, `r` and `r_rm` represent the 'types' an instruction works with. You can use any names you like. The first argument will be a `VM` instance, so _you can use its memory and registers right away_.

The last sentence is very important. You can code the instructions separately from the code for the `VM` class, yet it's possible to access _all_ the members of this class (normally, you'd only need memory and registers), even if your IDE tells you otherwise. Metaclass magic!

Each instruction shall occur after a header in the following form:

    ####################
    # MNEMONIC1 [/ MNEMONIC_i]*
    ####################
    
If you think you can implement multiple instructions as one class, it's OK, but please name it accordingly, like `ADDSUB` or `cbwcwde`, for example.

### Adding the instruction to the CPU

If you added a new `<category>` (see above), go to `VM/instructions/__init__.py` and add the following:

    from <your_category> import *

And this is it! Otherwise, you shouldn't even do anything because the instructions' implementations are collected and added to the CPU automagically using metaclasses. Remember, they _must_ be subclasses of `util.Instruction` for this to work!

### Adding the instruction mnemonic to README.md

This is simple: just add the instruction mnemonic to README.md in alphabetical order.
