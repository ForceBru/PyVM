import os
from io import UnsupportedOperation

from ..ctypes_types import udword, ctypes
from .kernel import Kernel, Int, Uint

import logging
logger = logging.getLogger(__name__)


class StructIovec(ctypes.LittleEndianStructure):
    """
    struct iovec
    {
        void * iov_base; / * Starting address * /
        size_t iov_len; / * Number of bytes to transfer * /
    };
    """
    _pack_ = 1
    _fields_ = [
        ('iov_base', udword),
        ('iov_len', udword)
    ]


@Kernel.register(0x05)
def sys_open(kernel: Kernel, pathname_addr: Uint, flags: Int, mode: Uint):
    """
    int open(const char *pathname, int flags, mode_t mode);
    """

    import enum

    class O_MODE(enum.IntFlag):
        """
        File access modes.
        See: https://github.com/torvalds/linux/blob/master/include/uapi/asm-generic/fcntl.h
        """
        O_ACCMODE = 0o00000003
        O_RDONLY = 0o00000000
        O_WRONLY = 0o00000001
        O_RDWR = 0o00000002
        O_CREAT = 0o00000100  # not fcntl
        O_EXCL = 0o00000200  # not fcntl
        O_NOCTTY = 0o00000400  # not fcntl
        O_TRUNC = 0o00001000  # not fcntl
        O_APPEND = 0o00002000
        O_NONBLOCK = 0o00004000
        O_DSYNC = 0o00010000  # used to be O_SYNC, see below
        FASYNC = 0o00020000  # fcntl, for BSD compatibility
        O_DIRECT = 0o00040000  # direct disk access hint
        O_LARGEFILE = 0o00100000
        O_DIRECTORY = 0o00200000  # must be a directory
        O_NOFOLLOW = 0o00400000  # don't follow links
        O_NOATIME = 0o01000000
        O_CLOEXEC = 0o02000000  # set close_on_exec

        _O_SYNC = 0o04000000
        O_SYNC = (_O_SYNC | O_DSYNC)
        O_PATH = 0o010000000

        _O_TMPFILE = 0o020000000
        # a horrid kludge trying to make sure that this will fail on old kernels
        O_TMPFILE = (_O_TMPFILE | O_DIRECTORY)
        O_TMPFILE_MASK = (_O_TMPFILE | O_DIRECTORY | O_CREAT)

    def open_file(name: str, mode: str):
        # find empty descriptor, starting from 3
        descriptor = -1
        for descr, file in enumerate(kernel.cpu.descriptors):
            if file is None:
                # found empty descriptor
                # print('found empty descriptor')
                descriptor = descr
                break

        if descriptor == -1:  # no empty descriptors found
            descriptor = len(kernel.cpu.descriptors)
            # print(f'opening new descriptor: {descriptor}')
            kernel.cpu.descriptors.append(open(name, mode))
        else:
            # print(f'reusing existing descriptor: {descriptor}')
            kernel.cpu.descriptors[descriptor] = open(name, mode)

        return descriptor

    pathname = kernel.kernel_read_string(pathname_addr).decode()
    flags = O_MODE(flags)
    mode = O_MODE(mode)
    logger.info('sys_open(const char *pathname=%r, int flags=%s, mode_t mode=%s)', pathname, flags, mode)

    if flags & O_MODE.O_RDONLY:
        if not os.path.exists(pathname):
            return -1

        descr = open_file(pathname, 'r')
        logger.info('\tsys_open: [SUCC] %s descriptor %u', flags, descr)

        return descr
    elif flags & O_MODE.O_WRONLY:
        if flags & O_MODE.O_TRUNC:
            descr = open_file(pathname, 'w')
        else:
            descr = open_file(pathname, 'x')

        logger.info('\tsys_open: [SUCC] %s descriptor %u', flags, descr)

        return descr
    elif flags & O_MODE.O_RDWR:
        if pathname == '/dev/tty':
            return 0  # TODO: what to do with TTYs?

        descr = open_file(pathname, 'r+')

        logger.info('\tsys_open: [SUCC] %s descriptor %u', flags, descr)

        return descr
    elif flags & O_MODE.O_LARGEFILE:  # open for reading?
        if pathname.startswith('/etc'):
            return -1

        descr = open_file(pathname, 'r')
        logger.info('\tsys_open: [SUCC] %s descriptor %u', flags, descr)

        return descr
    else:
        # TODO: do not know what to do with these yet...

        logger.info('\tsys_open: [ERR] %s do not know how to open', flags)
        return -1


@Kernel.register(0x06)
def sys_close(kernel: Kernel, fd: Uint):
    """
    sys_close(unsigned int fd)
    """

    logger.info('sys_close(unsigned int fd = %u)', fd)

    if fd >= len(kernel.cpu.descriptors):
        logger.info('\tsys_close: [ERR] descriptor %u not found', fd)
        return -1  # error

    if kernel.cpu.descriptors[fd] is None:  # kernel.cpu.descriptors[fd].closed:
        logger.info('\tsys_close: [ERR] descriptor %u already closed', fd)
        return -1  # error

    kernel.cpu.descriptors[fd].close()
    kernel.cpu.descriptors[fd] = None

    logger.info('\tsys_close: [SUCC] descriptor %u closed', fd)

    return 0


@Kernel.register(0x0a)
def sys_unlink(kernel: Kernel, pathname_addr: Uint):
    """
    int sys_unlink(const char * pathname)
    """

    pathname = kernel.kernel_read_string(pathname_addr).decode()

    logger.info('sys_unlink(const char * pathname = %r)', pathname)

    try:
        os.unlink(pathname)
    except OSError:
        ret = -1
        logger.info('\tsys_unlink: [ERR] failed to unlink %r', pathname)
    else:
        logger.info('\tsys_unlink: [SUCC] unlinked %r', pathname)
        ret = 0

    return ret


@Kernel.register(0x03)
def sys_read(kernel: Kernel, fd: Uint, data_addr: Uint, count: Uint):
    logger.info('sys_read(unsigned int fd = %u, char *dest = 0x%08x, size_t count = %u)', fd, data_addr, count)

    try:
        data = os.read(kernel.cpu.descriptors[fd].fileno(), count)
    except (AttributeError, UnsupportedOperation):
        data = (kernel.cpu.descriptors[fd].read(count) + '\n').encode('ascii')
    except:
        logger.error('\tsys_read: [ERR] failed to read %u bytes from descriptor %u', count, fd)

        return -1

    logger.info('\tsys_read: [SUCC] read %r from fd %u', data, fd)

    l = len(data)
    kernel.cpu.mem.set_bytes(data_addr, l, data)

    return l


@Kernel.register(0x04)
def sys_write(kernel: Kernel, fd: Uint, buf_addr: Uint, count: Uint):
    """
    Arguments: (unsigned int fd, const char * buf, size_t count)
    """

    buf = kernel.cpu.mem.get_bytes(buf_addr, count)

    logger.info('sys_write(%d, 0x%08x(%s), %d)', fd, buf_addr, buf, count)
    try:
        fileno = kernel.cpu.descriptors[fd].fileno()
        ret = os.write(fileno, buf)
        # os.fsync(fileno)
    except (AttributeError, UnsupportedOperation):
        ret = kernel.cpu.descriptors[fd].write(buf.decode('ascii'))
        kernel.cpu.descriptors[fd].flush()

    return ret if ret is not None else count


@Kernel.register(0x92)
def sys_writev(kernel: Kernel, fd: Int, iov_addr: Uint, iovcnt: Int):
    """
    ssize_t writev(
        int fd,  // file descriptor
        const struct iovec *iov,  // pointer to the beginning of an _array_ of structs
        int iovcnt  // number of elements in that array
        );

    The `writev()` system call writes `iovcnt` buffers of data described by
    `iov` to the file associated with the file descriptor `fd` ("gather output").

    TAKEN FROM: http://man7.org/linux/man-pages/man2/writev.2.html
    """

    logger.info('sys_writev(fd=%d, iov=0x%x, iovcnt=%d)', fd, iov_addr, iovcnt)

    size = 0
    for x in range(iovcnt):
        iovec = StructIovec.from_address(kernel.cpu.mem.calc_address(iov_addr))

        logger.info(
            'struct iovec {\n\tvoid *iov_base=0x%08x;\n\tsize_t iov_len=%d;\n}',
            iovec.iov_base, iovec.iov_len
        )

        if not iovec.iov_len:
            iov_addr += ctypes.sizeof(StructIovec)
            continue

        buf = kernel.cpu.mem.get_bytes(iovec.iov_base, iovec.iov_len)

        logger.info('iov_%d=0x%08x; iov_len=%d, buf=%s', x, iovec.iov_base, iovec.iov_len, buf)

        try:
            ret = os.write(kernel.cpu.descriptors[fd].fileno(), buf)
        except (AttributeError, UnsupportedOperation):
            ret = kernel.cpu.descriptors[fd].write(buf.decode('ascii'))
            kernel.cpu.descriptors[fd].flush()

        size += ret if ret is not None else iovec.iov_len
        iov_addr += ctypes.sizeof(StructIovec)  # address of the next struct!

    return size


@Kernel.register(0x8c)
def sys_llseek(kernel: Kernel, fd: Uint, offset_high: Uint, offset_low: Uint, result_addr: Uint, whence: Uint):
    """
    Arguments: (unsigned int fd, unsigned long offset_high,
               unsigned long offset_low, loff_t *result,
               unsigned int whence)

    See: http://man7.org/linux/man-pages/man2/llseek.2.html
    """

    logger.info('sys_lseek(fd=%d, offset_high=%d, offset_low=%d, result=0x%08x, whence=%d)',
                fd, offset_high, offset_low, result_addr, whence
                )

    offset = (offset_high << 32) | offset_low

    try:
        descriptor = kernel.cpu.descriptors[fd].fileno()
    except AttributeError:
        kernel.cpu.mem.set(result_addr, 4, 0)
        return 0

    try:
        os.lseek(descriptor, offset & 0xFFFFFFFF, whence)
        ret = 0
    except OSError:
        kernel.cpu.mem.set(result_addr, 4, -1)
        return -1
    else:
        kernel.cpu.mem.set(result_addr, 4, ret)

    # return success
    return ret

