from .debug import debug
from .util import to_int
import os

from io import UnsupportedOperation


class SyscallsMixin_Meta(type):
    def __new__(cls, name, bases, dict):
        syscalls = {
            y.__defaults__[0]: y
            for x, y in dict.items()
            if x.startswith('sys_')
        }

        for syscall in syscalls.values():
            dict[syscall.__name__] = syscall

        dict['valid_syscalls_names'] = {code: fn.__name__ for code, fn in syscalls.items()}

        # make `type` the metaclass, otherwise there'll be a metaclass conflict
        return type(name, bases, dict)


class SyscallsMixin(metaclass=SyscallsMixin_Meta):
    def sys_py_dbg(self, code=0x00):
        raw = self.reg.get(3, 4)
        data = to_int(raw)  # EBX
        _type = to_int(self.reg.get(1, 4))  # ECX

        if _type == 0:  # treat as pointer to char
            addr = data
            buffer = bytearray()
            byte, = self.mem.get(addr, 1)
            while byte != 0:
                buffer.append(byte)
                addr += 1
                byte, = self.mem.get(addr, 1)

            print(f'[PY_DBG_STRING] {buffer.decode()}')
        elif _type == 1:  # treat as unsigned integer
            print(f'[PY_DBG_UINT] {data}')
        elif _type == 2:  # treat as signed integer
            print(f'[PY_DBG_INT] {to_int(raw, True)}')
        else:
            print(f'[PY_DBG_UNRECOGNIZED] {raw}')

    def sys_exit(self, code=0x01):
        code = to_int(self.reg.get(3, 4), True)  # EBX

        self.descriptors[2].write('[!] Process exited with code {}\n'.format(code))
        self.RETCODE = code
        self.running = False

    def sys_read(self, code=0x03):
        fd = to_int(self.reg.get(3, 4))  # EBX
        data_addr = to_int(self.reg.get(1, 4))  # ECX
        count = to_int(self.reg.get(2, 4))  # EDX

        try:
            data = os.read(self.descriptors[fd].fileno(), count)
        except (AttributeError, UnsupportedOperation):
            data = (self.descriptors[fd].read(count) + '\n').encode('ascii')

        if debug: print('sys_read({}, {}({}), {})'.format(fd, data_addr, data, count))
        self.mem.set(data_addr, data)
        self.reg.set(0, len(data).to_bytes(4, 'little'))

    def sys_write(self, code=0x04):
        """
        Arguments: (unsigned int fd, const char * buf, size_t count)
        """
        fd = to_int(self.reg.get(3, 4), signed=1)  # EBX
        buf_addr = to_int(self.reg.get(1, 4))  # ECX
        count = to_int(self.reg.get(2, 4), signed=1)  # EDX

        buf = self.mem.get(buf_addr, count)

        if debug: print('sys_write({}, {}({}), {})'.format(fd, buf_addr, buf, count))
        try:
            ret = os.write(self.descriptors[fd].fileno(), buf)
        except (AttributeError, UnsupportedOperation):
            ret = self.descriptors[fd].write(buf.decode('ascii'))
            self.descriptors[fd].flush()

        size = ret if ret is not None else count

        self.reg.set(0, size.to_bytes(4, 'little'))

    def sys_brk(self, code=0x2d):
        '''
        Arguments: (unsigned long brk)

        https://elixir.bootlin.com/linux/v2.6.35/source/mm/mmap.c#L245
        '''
        brk = to_int(self.reg.get(3, 4))  # EBX

        min_brk = self.code_segment_end

        if brk < min_brk:
            print(f'\t\tSYS_BRK: invalid break: {brk} < {min_brk}; return {self.mem.program_break}')
            self.reg.set(0, self.mem.program_break.to_bytes(4, 'little'))
            return

        newbrk = brk
        oldbrk = self.mem.program_break

        if oldbrk == newbrk:
            print(f'\t\tSYS_BRK: not changing break: {oldbrk} == {newbrk}')
            self.reg.set(0, oldbrk.to_bytes(4, 'little'))
            return

        self.mem.program_break = brk

        print(f'\t\tSYS_BRK: changing break: {oldbrk} -> {self.mem.program_break} ({self.mem.program_break - oldbrk:+d})')
        self.reg.set(0, self.mem.program_break.to_bytes(4, 'little'))
