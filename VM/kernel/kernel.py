from typing import Callable

from ..ctypes_types import dword as Int, udword as Uint


import logging
logger = logging.getLogger(__name__)


class KernelMeta(type):   
    def register(cls, syscall_number: int):
        def actually_register(function: Callable[..., int]):
            assert syscall_number not in cls.syscalls, f'Duplicate syscall {syscall_number} -> {function}'
            assert not hasattr(cls, function.__name__), f'Duplicate syscall name: {function.__name__} already bound to {getattr(cls, function.__name__)}'
            
            arg_types = tuple(function.__annotations__.values())
            
            if arg_types and arg_types[0] is Kernel:
                arg_types = arg_types[1:]
                assert len(arg_types) == function.__code__.co_argcount - 1, f'Not all arguments of syscall {function} have annotations'
            else:
                assert len(arg_types) == function.__code__.co_argcount, f'Not all arguments of syscall {function} have annotations'
            
            logger.info('registering syscall 0x%02x-> %r', syscall_number, function.__name__)
            cls.syscalls[syscall_number] = function, arg_types
            setattr(cls, function.__name__, function)
            
            return function       
        return actually_register


class Kernel(metaclass=KernelMeta):
    reg_numbers = [3, 1, 2, 6, 7]  # ebx, ecx, edx, esi, edi
    syscalls = {}

    def __init__(self, cpu):
        self.cpu = cpu
        self.free_memory_blocks = []
        
    def __getitem__(self, syscall_number: int):
        try:
            impl, args_types = self.syscalls[syscall_number]
        except KeyError:
            raise KeyError(f'Syscall 0x{syscall_number:02x} not found')
            
        actual_args = (
            self.cpu.reg.get(x, 4, signed=arg_type is Int)
            for x, arg_type in zip(self.reg_numbers, args_types)
        )
        return lambda: impl(self, *actual_args)

    def kernel_read_string(self, address: int) -> bytes:
        return self.cpu.mem.kernel_read_string(address)

