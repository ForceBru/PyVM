from .debug import debug
from .util import to_int
import os

from io import UnsupportedOperation

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
        return self.program_break
        
    newbrk = brk
    oldbrk = self.program_break
    
    if oldbrk == newbrk:
        return oldbrk
        
    self.program_break = brk
    
class SyscallsMixin_Meta(type):
    def __new__(cls, name, bases, dict):
        syscalls = {
            y.__defaults__[0]: y
            for x,y in globals().items()
            if x.startswith('sys_')
        }
        
        for syscall in syscalls.values():
            dict[syscall.__name__] = syscall
            
        dict['valid_syscalls_names'] = {code: fn.__name__ for code, fn in syscalls.items()}
        
        # make `type` the metaclass, otherwise there'll be a metaclass conflict
        return type(name, bases, dict)
    
class SyscallsMixin(metaclass=SyscallsMixin_Meta):
    ...
    
