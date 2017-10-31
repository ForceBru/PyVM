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

    if debug: print('sys_read({}, {}({}), {})'.format(fd, data_addr, data, count))
    self.mem.set(data_addr, data)
    self.reg.set(0, len(data).to_bytes(4, 'little'))


def sys_write(self):
    """
    Arguments: (unsigned int fd, const char * buf, size_t count)
    """
    fd = to_int(self.reg.get(3, 4), signed=1)  # EBX
    buf_addr = to_int(self.reg.get(1, 4))  # ECX
    count = to_int(self.reg.get(2, 4), signed=1)  # EDX

    buf = self.mem.get(buf_addr, count)

    if debug: print('sys_write({}, {}({}), {})'.format(fd, buf_addr, buf, count))
    ret = self.descriptors[fd].write(buf.decode(errors='replace'))
    self.reg.set(0, ret.to_bytes(4, 'little'))
