from .debug import debug
from .CPU import to_int


def sys_exit(self):
    code = to_int(self.reg.get(3, 4), True)  # EBX

    self.descriptors[2].write('[!] Process exited with code {}\n'.format(code))
    self.running = False


def sys_read(self):
    fd = to_int(self.reg.get(3, 4))  # EBX
    data_addr = to_int(self.reg.get(1, 4))  # ECX
    count = to_int(self.reg.get(2, 4))  # EDX

    data = self.descriptors[fd].read(count)

    debug('sys_read({}, {}({}), {})'.format(fd, data_addr, data, count))
    self.mem.set(data_addr, data)


def sys_write(self):
    fd = to_int(self.reg.get(3, 4), signed=1)  # EBX
    data_addr = to_int(self.reg.get(1, 4))  # ECX
    count = to_int(self.reg.get(2, 4), signed=1)  # EDX

    data = self.mem.get(data_addr, count)

    debug('sys_write({}, {}({}), {})'.format(fd, data_addr, data, count))
    self.descriptors[fd].write(data.decode(errors='replace'))
