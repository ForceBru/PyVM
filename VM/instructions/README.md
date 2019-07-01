# PyVM - execute x86 bytecode in pure Python!

[![Build Status](https://travis-ci.org/ForceBru/PyVM.svg?branch=master)](https://travis-ci.org/ForceBru/PyVM)

PyVM executes x86 (IA-32) bytecode in _pure Python_, without any dependencies.

------

This is where the instructions are implemented.

Each instruction should derive from `..util.Instruction` in order to be properly registered.
<sub>The registration protocol is kinda weird right now...</sub>

The instruction has access to all attributes of the CPU, like the registers, memory, ModRM byte parsing etc, _but not other instructions_.
Each instruction consists of two parts: the opcode map and the actual implementations.

```python
from functools import partialmethod as P

from ..utils import Instruction


class SomeInstruction(Instruction):
    # BEGIN opcode map
    def __init__(self):
        # These instructions are just examples
        self.opcodes = {
            0x00: P(self.variant1, is_8bit=True),
            0x01: P(self.variant1, is_8bit=False),
            
            # Some instructions may have a common implementation that only depends on some parameters, like the REG field of the ModRM byte
            0x02: [
                P(self.common_impl, REG=0),  # ADD r/m8, imm8
                P(self.common_impl, REG=5),  # SUB r/m8, imm8
                P(self.common_impl, REG=7),  # CMP r/m8, imm8
                P(self.common_impl, REG=2),  # ADC r/m8, imm8
                P(self.common_impl, REG=3),  # SBB r/m8, imm8
            ],
            0x03: self.simple_impl,
            0x0F04: P(self.decide, REG=3)
        }
    # END opcode map
        
    # BEGIN implementation
    def variant1(vm, is_8bit: bool) -> True:
        size = 1 if is_8bit else vm.operand_size
        data = vm.reg.get(0, size)
         
        vm.mem.set(0, size, data)
        
        return True
        
    def common_impl(vm, REG: int) -> True:
        if REG == 0:
            ...  # do something
        elif REG == 5:
            ...  # do something else
        ...
        
        return True
        
    def simple_impl(vm) -> True:
        ...  # Does not depend on any arguments
        return True
        
    def decide(vm, REG: int) -> bool:
        # Check if this implementation is the correct one.
        ModRM = vm.mem.get_eip(vm.eip, 1)
        _REG = (ModRM & 0b00111000) >> 3  # This is the actual REG field of the ModRM byte

        if _REG != REG:  # If the actual field does not equal the desired one, this is not the right implementation...
            # ...thus, backtrack and try another one
            return False
            
        # This is the correct implementation for the current opcode.
        RM, R = vm.process_ModRM()  # Get the operands.
        ...  # Execute the instruction here
        return True
    # END implementation
```

This looks more like a backtracking parser that executes the opcode once it finds the matching implementation.