from .debug import debug
from .util import to_int, byteorder, segment_descriptor_struct
import os
import struct

import logging
logger = logging.getLogger(__name__)

struct_iovec = struct.Struct('<II')
struct_user_desc = struct.Struct('<ILIBH4B')

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
    def __read_string(self, address: int):
        ret = bytearray()
        
        byte, = self.mem.get(address, 1)
        while byte != 0:
            ret.append(byte)
            address += 1
            byte, = self.mem.get(address, 1)
            
        return ret
        
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
        
    def sys_set_thread_area(self, code=0xf3):
        """
        Arguments: (struct user_desc *u_info)

        Docs: http://man7.org/linux/man-pages/man2/set_thread_area.2.html

        // TAKEN FROM: http://man7.org/linux/man-pages/man2/set_thread_area.2.html
        struct user_desc {
            unsigned int  entry_number;
            unsigned long base_addr;
            unsigned int  limit;
            unsigned int  seg_32bit:1;
            unsigned int  contents:2;
            unsigned int  read_exec_only:1;
            unsigned int  limit_in_pages:1;
            unsigned int  seg_not_present:1;
            unsigned int  useable:1;
        };
        """
        u_info_addr = to_int(self.reg.get(3, 4))  # EBX
        
        logger.debug(f'sys_set_thread_area(u_info=0x%x)', u_info_addr)

        u_info = struct_user_desc.unpack(self.mem.get(u_info_addr, struct_user_desc.size))

        logger.debug(
            """
struct user_desc {
    unsigned int  entry_number      = %d;
    unsigned long base_addr         = %d;
    unsigned int  limit             = %d;
    unsigned int  seg_32bit:1       = %d;
    unsigned int  contents:2        = %d;
    unsigned int  read_exec_only:1  = %d;
    unsigned int  limit_in_pages:1  = %d;
    unsigned int  seg_not_present:1 = %d;
    unsigned int  useable:1         = %d;
};""", *u_info)

        """
        A `user_desc` is considered "empty" if `read_exec_only` and
       `seg_not_present` are set to 1 and all of the other fields are 0.  If
       an "empty" descriptor is passed to `set_thread_area()`, the correspond‐
       ing TLS entry will be cleared.
        """

        selector_index = 0
        if u_info[0] == 4294967295:  # a.k.a. (unsigned int)(-1)
            """
            When set_thread_area() is passed an entry_number of -1, it searches
            for a free TLS entry.  If set_thread_area() finds a free TLS entry,
            the value of u_info->entry_number is set upon return to show which
            entry was changed.
            """

            for selector_index, entry in enumerate(self.GDT):
                base3, limit2, info, base2, base1, limit1 = segment_descriptor_struct.unpack(entry)
                segment_present = (info >> 8) & 1

                if segment_present:
                    continue

                base_addr = u_info[1]

                # BEGIN set up BASE
                base1 = base_addr & 0xFFFF
                base3 = (base_addr >> 24) & 0xFF
                base2 = (base_addr >> 16) & 0xFF
                # END set up BASE

                limit = u_info[2]

                # BEGIN set up LIMIT
                limit1 = limit & 0xFFFF

                limit2 &= 0xF0  # clear limit2
                limit2 += (limit >> 16) & 0xF
                # END set up LIMIT

                info |= 1 << 7  # set segment present to True

                descriptor = base3, limit2, info, base2, base1, limit1

                self.GDT[selector_index] = segment_descriptor_struct.pack(
                    *descriptor
                )

                break

        self.mem.set(u_info_addr, selector_index.to_bytes(4, byteorder))  # set address of new selector
        # return success (0) or error (-1)
        self.reg.set(0, (0).to_bytes(4, 'little', signed=True))
        
    def sys_modify_ldt(self, code=0x7b):
        """
        Arguments: (int func, void *ptr, unsigned long bytecount)

        modify_ldt() reads or writes the local descriptor table (LDT) for a
       process.
        """

        func = to_int(self.reg.get(3, 4))  # EBX
        ptr_addr = to_int(self.reg.get(1, 4))  # ECX
        bytecount = to_int(self.reg.get(2, 4))  # EDX

        if debug: print(f'modify_ldt(func={func}, ptr={ptr_addr:04x}, bytecount={bytecount})')
        # do nothing, return error
        self.reg.set(0, (-1).to_bytes(4, 'little', signed=True))
        
    def sys_set_tid_address(self, code=0x102):
        """
        Arguments: (int *tidptr)

        The system call set_tid_address() sets the clear_child_tid value for
       the calling thread to tidptr.

        :return: always returns the caller's thread ID.
        """

        tidptr = to_int(self.reg.get(3, 4))  # EBX

        tid = self.mem.get(tidptr, 4)

        logger.debug(f'sys_set_tid_address(tidptr={tidptr:04x} (tid={tid}))')

        # do nothing, return tid (thread ID)
        self.reg.set(0, tid)

    def sys_exit_group(self, code=0xfc):
        return self.sys_exit()

    def sys_writev(self, code=0x92):
        """
        ssize_t writev(
            int fd,  // file descriptor
            const struct iovec *iov,  // pointer to the beginning of an _array_ of structs
            int iovcnt  // number of elements in that array
            );

        The `writev()` system call writes `iovcnt` buffers of data described by
        `iov` to the file associated with the file descriptor `fd` ("gather output").

        TAKEN FROM: http://man7.org/linux/man-pages/man2/writev.2.html

        struct iovec
        {
            void * iov_base; / * Starting address * /
            size_t iov_len; / * Number of bytes to transfer * /
        };
        """

        fd = to_int(self.reg.get(3, 4), signed=1)  # EBX
        iov_addr = to_int(self.reg.get(1, 4))  # ECX
        iovcnt = to_int(self.reg.get(2, 4), signed=1)  # EDX

        logger.debug('sys_writev(fd=%d, iov=0x%x, iovcnt=%d)', fd, iov_addr, iovcnt)

        size = 0
        for x in range(iovcnt):
            iov_base, iov_len = struct_iovec.unpack(self.mem.get(iov_addr, struct_iovec.size))

            logger.debug('struct iovec {\n\tvoid *iov_base=0x%x;\n\tsize_t iov_len=%d;\n}', iov_base, iov_len)

            if not iov_len:
                iov_addr += struct_iovec.size
                continue

            buf = self.mem.get(iov_base, iov_len)

            logger.debug('iov_%d=0x%x; iov_len=%d, buf=%s', x, iov_base, iov_len, buf)

            try:
                ret = os.write(self.descriptors[fd].fileno(), buf)
            except (AttributeError, UnsupportedOperation):
                ret = self.descriptors[fd].write(buf.decode('ascii'))
                self.descriptors[fd].flush()

            size += ret if ret is not None else iov_len
            iov_addr += struct_iovec.size  # address of the next struct!

        self.reg.set(0, size.to_bytes(4, 'little'))

    def sys_ioctl(self, code=0x36):
        """
        Arguments: (int fd, unsigned long request, ...)
        """
        fd = to_int(self.reg.get(3, 4), signed=1)  # EBX
        request = to_int(self.reg.get(1, 4))  # ECX
        data_addr = to_int(self.reg.get(2, 4))  # EDX

        # SOURCE: http://man7.org/linux/man-pages/man2/ioctl_list.2.html
        # < include / asm - i386 / termios.h >
        #
        # 0x00005401 TCGETS struct termios *
        # 0x00005402 TCSETS const struct termios *
        # 0x00005403 TCSETSW const struct termios *
        # 0x00005404 TCSETSF const struct termios *
        # 0x00005405 TCGETA struct termio *
        # 0x00005406 TCSETA const struct termio *
        # 0x00005407 TCSETAW const struct termio *
        # 0x00005408 TCSETAF const struct termio *
        # 0x00005409 TCSBRK int
        # 0x0000540A TCXONC int
        # 0x0000540B TCFLSH int
        # 0x0000540C TIOCEXCL void
        # 0x0000540D TIOCNXCL void
        # 0x0000540E TIOCSCTTY int
        # 0x0000540F TIOCGPGRP pid_t *
        # 0x00005410 TIOCSPGRP const pid_t *
        # 0x00005411 TIOCOUTQ int *
        # 0x00005412 TIOCSTI const char *
        # 0x00005413 TIOCGWINSZ struct winsize *
        # 0x00005414 TIOCSWINSZ const struct winsize *
        # 0x00005415 TIOCMGET int *
        # 0x00005416 TIOCMBIS const int *
        # 0x00005417 TIOCMBIC const int *
        # 0x00005418 TIOCMSET const int *
        # 0x00005419 TIOCGSOFTCAR int *
        # 0x0000541A TIOCSSOFTCAR const int *
        # 0x0000541B FIONREAD int *
        # 0x0000541B TIOCINQ int *
        # 0x0000541C TIOCLINUX const char * // MORE
        # 0x0000541D TIOCCONS void
        # 0x0000541E TIOCGSERIAL struct serial_struct *
        # 0x0000541F TIOCSSERIAL const struct serial_struct *
        # 0x00005420 TIOCPKT const int *
        # 0x00005421 FIONBIO const int *
        # 0x00005422 TIOCNOTTY void
        # 0x00005423 TIOCSETD const int *
        # 0x00005424 TIOCGETD int *
        # 0x00005425 TCSBRKP int
        # 0x00005426 TIOCTTYGSTRUCT struct tty_struct *
        # 0x00005450 FIONCLEX void
        # 0x00005451 FIOCLEX void
        # 0x00005452 FIOASYNC const int *
        # 0x00005453 TIOCSERCONFIG void
        # 0x00005454 TIOCSERGWILD int *
        # 0x00005455 TIOCSERSWILD const int *
        # 0x00005456 TIOCGLCKTRMIOS struct termios *
        # 0x00005457 TIOCSLCKTRMIOS const struct termios *
        # 0x00005458 TIOCSERGSTRUCT struct async_struct *
        # 0x00005459 TIOCSERGETLSR int *
        # 0x0000545A TIOCSERGETMULTI struct serial_multiport_struct *
        # 0x0000545B TIOCSERSETMULTI const struct serial_multiport_struct *

        import enum
        directions = enum.Flag('directions', '_IOC_NONE _IOC_READ _IOC_WRITE', start=0)

        # TAKEN FROM: https://elixir.bootlin.com/linux/v5.0.8/source/include/uapi/asm-generic/ioctl.h
        _IOC_NRBITS   = 8
        _IOC_TYPEBITS = 8
        _IOC_SIZEBITS = 14
        _IOC_DIRBITS  = 2

        _IOC_NRMASK = ((1 << _IOC_NRBITS)-1)
        _IOC_TYPEMASK = ((1 << _IOC_TYPEBITS)-1)
        _IOC_SIZEMASK = ((1 << _IOC_SIZEBITS)-1)
        _IOC_DIRMASK = ((1 << _IOC_DIRBITS)-1)

        _IOC_NRSHIFT = 0
        _IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
        _IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
        _IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS

        _IOC_NONE = 0
        _IOC_WRITE = 1
        _IOC_READ = 2

        _IOC_DIR = lambda nr: (((nr) >> _IOC_DIRSHIFT) & _IOC_DIRMASK)
        _IOC_TYPE = lambda nr: (((nr) >> _IOC_TYPESHIFT) & _IOC_TYPEMASK)
        _IOC_NR = lambda nr: (((nr) >> _IOC_NRSHIFT) & _IOC_NRMASK)
        _IOC_SIZE = lambda nr: (((nr) >> _IOC_SIZESHIFT) & _IOC_SIZEMASK)

        IOC_IN = (_IOC_WRITE << _IOC_DIRSHIFT)
        IOC_OUT = (_IOC_READ << _IOC_DIRSHIFT)
        IOC_INOUT = ((_IOC_WRITE|_IOC_READ) << _IOC_DIRSHIFT)
        IOCSIZE_MASK = (_IOC_SIZEMASK << _IOC_SIZESHIFT)
        IOCSIZE_SHIFT = (_IOC_SIZESHIFT)

        request_type = bytes([_IOC_TYPE(request)])
        request_number = _IOC_NR(request)
        request_direction = directions(_IOC_DIR(request))
        request_size = _IOC_SIZE(request)

        if debug: print(f'ioctl(fd={fd},request={request:09_x} (type={request_type}, number={request_number}, direction={request_direction}, size={request_size}))')

        if request_type == b'T':
            if request_number == 19 and request_direction == directions._IOC_NONE:
                try:
                    self.descriptors[fd]
                except IndexError:
                    self.reg.set(1, (-1).to_bytes(4, 'little', signed=True))
                    return

                # TAKEN FROM: http://man7.org/linux/man-pages/man4/tty_ioctl.4.html
                #
                # struct winsize
                # {
                #     unsigned short ws_row;
                #     unsigned short ws_col;
                #     unsigned short ws_xpixel; / *unused * /
                #     unsigned short ws_ypixel; / *unused * /
                # };
                struct_winsize = struct.Struct('<HHHH')

                self.mem.set(data_addr, struct_winsize.pack(256, 256, 0, 0))
                self.reg.set(0, (0).to_bytes(4, 'little'))
                return
        self.reg.set(0, (-1).to_bytes(4, 'little', signed=True))
