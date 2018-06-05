"""
This module accumulates all the instructions' implementations. It is necessary to import them like this so that they
could be registered properly.

The individual implementations are structured in the following way:
    An instruction (or some very similar instructions) is represented by a class, whose parent must be 'util.Instruction'.
    This class must have an '__init__' method, where an attribute called 'opcodes' must be created:

    Example:
        from ..util import Instruction


        class INSTRUCTION(Instruction):
            def __init__(self):
                self.opcodes = {
                    0x00: [
                        self.do_that,
                        self.do_another_thing  # yes, one opcode may represent two instructions
                        ],
                    0x01: self.do_this
                    }

            def do_that(self):
                print("Hello!")

                return True # indicate success

            def do_another_thing(self):
                print("Hello, world!")

                return True # indicate success

            def do_this(self):
                print("Hey!")

                return True # indicate success

    Later on, all classes inheriting from 'util.Instruction' are automatically registered, and their methods become
     methods of the 'CPU.CPU32' class.
"""

from .bitwise import *
from .control import *
from .math import *
from .memory import *