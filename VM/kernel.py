if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class Kernel:
    syscalls = {}

    def __init__(self, cpu):
        self.cpu = cpu
        self.free_memory_blocks = []

    def kernel_read_string(self, address: int) -> bytes:
        return self.cpu.mem.kernel_read_string(address)

    def kernel_args(self, types: str):
        """

        :param types: Indicates signed ('s') or unsigned types.
        Example:
            'sus' => arguments 1 and 3 are signed, argument 2 is unsigned
        :return:
        """
        registers = [3, 1, 2, 6, 7]  # ebx, ecx, edx, esi, edi

        return (self.cpu.reg.get(reg, 4, signed=type == 's') for reg, type in zip(registers, types))

    @classmethod
    def register(cls, function, syscall_number: int):
        assert syscall_number not in cls.syscalls, f'Duplicate system call: {syscall_number} is alreay bound to {cls.syscalls[syscall_number].__name__}'

        cls.syscalls[syscall_number] = function

        if __debug__:
            logger.info('Registered syscall %r: %02x', function.__name__, syscall_number)

    def syscall(self, syscall_number: int):
        function = self.syscalls.get(syscall_number, None)

        if function is None:
            return False

        self.cpu.reg.eax = function(self)
