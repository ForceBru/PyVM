import functools
import os
import binascii
import enum
import struct
import logging
logger = logging.getLogger(__name__)


byteorder = 'little'
SegmentRegs = enum.IntEnum('SegmentRegs', 'ES CS SS DS FS GS', start=0)  # see vol. 2A 3.1.1.3 Sreg
segment_descriptor_struct = struct.Struct('<4B2H')  # see vol. 3A 3.4.5


def to_int(data: bytes, signed=False):
    return int.from_bytes(data, byteorder, signed=signed)


class InstructionMeta(type):
    """
    This metaclass simply registers all the classes that inherit from 'Instruction' (see below).
    """
    instruction_set = set()

    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)

        if name == 'Instruction':
            return

        logger.log(logging.NOTSET, "Registering instruction %s...", name)

        if '__init__' not in dct.keys():
            raise AttributeError("Instructions must have an '__init__' method")

        if cls in cls.__class__.instruction_set:
            raise ValueError(f"Duplicate instruction: {name}")

        setattr(cls, '__init__', lambda self: dct['__init__'](cls))
        cls.__class__.instruction_set.add(cls)

        logger.log(logging.NOTSET, "\tInstruction %s registered", name)


class CPUMeta(type):
    """
    This metaclass transfers all the needed methods of all the registered instructions' classes into the name space of 'cls'.
    Duplicate function names are handled accordingly.
    """
    
    loaded = False
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        
        if cls.__class__.loaded or not Instruction.instruction_set:
            # Metaclasses are called _on class creation_, so this will be called
            # for every class that uses this metaclass, which will result in
            # duplicates of opcode implementations.
            return

        cls._opcodes_names = {} # TODO: this looks ugly
        cls._concrete_names = []

        for instruction in Instruction.instruction_set:
            for opcode, implementation in instruction().opcodes.items():
                if isinstance(implementation, (list, tuple)):  # in case one opcode represents two instructions
                    for impl in implementation:
                        CPUMeta.load_instruction(cls, instruction, opcode, impl)
                else:
                    CPUMeta.load_instruction(cls, instruction, opcode, implementation)
                    
        cls.__class__.loaded = True

    @staticmethod
    def load_instruction(cls, instruction, opcode, implementation):
        try:
            impl_name = implementation.__name__
        except AttributeError:
            if isinstance(implementation, functools.partialmethod):
                rand = binascii.hexlify(os.urandom(4)).decode()

                try:
                    impl_name = f"{implementation.func.__name__}_{rand}"
                except AttributeError:
                    # TODO: WTF is happening here? Eg. when wrapping a MagicMock
                    impl_name = rand
            else:
                # TODO: WTF is happening here? Eg. with a MagicMock
                impl_name = binascii.hexlify(os.urandom(4)).decode()
                # raise ValueError(f"Failed to retrieve function name for {implementation}")

        concrete_name = f"i_{instruction.__name__}_{impl_name}"

        while concrete_name in cls._concrete_names:
            concrete_name += binascii.hexlify(os.urandom(4)).decode()

        cls._concrete_names.append(concrete_name)

        setattr(cls, concrete_name, implementation)
        cls._opcodes_names.setdefault(opcode, []).append(concrete_name)


class Instruction(metaclass=InstructionMeta):
    """
    This class is here for convenience purposes only since it's much simpler (a.k.a. easier to type) to inherit from a class
     than to use some weird metaclass. Also, all classes inheriting this one are automagically registered by the metaclass.
    """
    ...


class CPU(metaclass=CPUMeta):
    """
    Thanks to the metaclass, all the methods of the registered instructions that are mentioned in their 'opcodes' attribute
     become bound to this class. The methods' names are handled accordingly by the metaclass.
    """
    def __init__(self):
        """
        This merely collects all the methods (which are now bound to the class), so that later on, 'self.instr[opcode]'
         would be a list containing all the instructions' implementations that correspond to that opcode.
        All the methods' names are stored in 'self._opcodes_names', which is kinda ugly, but... it works, so there's that.
        """
        self.instr = {
            opcode: {getattr(self, name) for name in impl_names}

            for opcode, impl_names in self._opcodes_names.items()
            }
