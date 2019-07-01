import struct
import ctypes

from .kernel import Kernel, Uint, Int

import logging
logger = logging.getLogger(__name__)


class StructNewUtsname(ctypes.LittleEndianStructure):
    """
    // See: https://elixir.bootlin.com/linux/v2.6.35/source/include/linux/utsname.h#L24
    struct new_utsname {
        char sysname[__NEW_UTS_LEN + 1];
        char nodename[__NEW_UTS_LEN + 1];
        char release[__NEW_UTS_LEN + 1];
        char version[__NEW_UTS_LEN + 1];
        char machine[__NEW_UTS_LEN + 1];
        char domainname[__NEW_UTS_LEN + 1];
    };
    """
    __NEW_UTS_LEN = 64 + 1
    _pack_ = 1
    _fields_ = [
        ('sysname', ctypes.c_char * __NEW_UTS_LEN),
        ('nodename', ctypes.c_char * __NEW_UTS_LEN),
        ('release', ctypes.c_char * __NEW_UTS_LEN),
        ('version', ctypes.c_char * __NEW_UTS_LEN),
        ('machine', ctypes.c_char * __NEW_UTS_LEN),
        ('domainname', ctypes.c_char * __NEW_UTS_LEN),
    ]


@Kernel.register(0x109)
def sys_clock_gettime(kernel: Kernel, clk_id: Uint, tp_addr: Uint):
    """
    int clock_gettime(clockid_t clk_id, struct timespec *tp);

    The functions clock_gettime() and clock_settime() retrieve and set
   the time of the specified clock clk_id.

   The res and tp arguments are timespec structures, as specified in
   <time.h>:

    struct timespec {
        time_t   tv_sec;        /* seconds */
        long     tv_nsec;       /* nanoseconds */
    };
    """

    struct_timespec = struct.Struct('<II')

    import time

    time_nanoseconds = int(time.time() * 1_000_000_000)  # Python 3.6 compatibility
    sec, nsec = time_nanoseconds // 1_000_000_000, time_nanoseconds % 1_000_000_000

    kernel.cpu.mem.set_bytes(tp_addr, struct_timespec.size, struct_timespec.pack(sec, nsec))

    return 0


@Kernel.register(0x36)
def sys_ioctl(kernel: Kernel, fd: Int, request: Uint, data_addr: Uint):
    """
    Arguments: (int fd, unsigned long request, ...)
    """

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

    logger.info(f'ioctl(fd={fd},request={request:09_x} (type={request_type}, number={request_number}, direction={request_direction}, size={request_size}))')

    if request_type == b'T':
        if request_number == 19 and request_direction == directions._IOC_NONE:
            try:
                kernel.cpu.descriptors[fd]
            except IndexError:
                return kernel.cpu.__return(-1)

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

            kernel.cpu.mem.set_bytes(data_addr, struct_winsize.size, struct_winsize.pack(256, 256, 0, 0))

            return 0

    return -1


@Kernel.register(0x01)
def sys_exit(kernel: Kernel, code: Int):
    # deallocate memory
    logger.info('sys_exit: deallocating memory...')
    oldbrk = kernel.cpu.mem.program_break
    kernel.sys_brk(kernel.cpu.code_segment_end)
    if oldbrk > kernel.cpu.mem.program_break:
        logger.info('sys_exit: %d bytes of memory deallocated', oldbrk - kernel.cpu.mem.program_break)
    else:
        logger.info('sys_exit: no memory to deallocate')

    logger.info('sys_exit: closing file descriptors...')
    closed = 0
    for i, descr in enumerate(kernel.cpu.descriptors[3:], 3):
        if descr is not None:
            if not descr.closed:
                closed += 1
                kernel.cpu.descriptors[i].close()
            kernel.cpu.descriptors[i] = None
    kernel.cpu.descriptors = list(filter(None, kernel.cpu.descriptors))
    if closed > 0:
        logger.info('sys_exit: closed %d file descriptors', closed)
    else:
        logger.info('sys_exit: no file descriptors to be closed')

    code &= 0o0377
    kernel.cpu.descriptors[2].write(f'[!] Process exited with code {code}\n')
    kernel.cpu.RETCODE = code
    kernel.cpu.running = False

    return code


@Kernel.register(0xfc)
def sys_exit_group(kernel: Kernel, code: Int):
    return sys_exit(kernel, code)


@Kernel.register(0x7a)
def sys_newuname(kernel: Kernel, buf_addr: Uint):
    """
    int sys_newuname(struct new_utsname *buf);
    """

    logger.debug(f'sys_newuname(struct new_utsname *buf=0x%08X)', buf_addr)

    uname = StructNewUtsname(
        sysname=b'PyVM_Linux',
        nodename=b'PyVM_Linux',
        release=b'3.14',
        version=b'3.14',
        machine=b'PyVM - Intel IA-32 on Python',
        domainname=b'PyVM_Linux.local'
    )

    kernel.cpu.mem.set_bytes(buf_addr, ctypes.sizeof(StructNewUtsname), bytes(uname))

    return 0

