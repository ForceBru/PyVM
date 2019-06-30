from .kernel import Kernel

from ctypes import LittleEndianStructure, c_uint32, sizeof

import logging
logger = logging.getLogger(__name__)


udword = c_uint32.__ctype_le__


class structUserDesc(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('entry_number', udword),
        ('base_addr', udword),
        ('limit', udword),
        ('seg_32bit', udword, 1),
        ('contents', udword, 2),
        ('read_exec_only', udword, 1),
        ('limit_in_pages', udword, 1),
        ('seg_not_present', udword, 1),
        ('useable', udword, 1),

    ]

    def __str__(self):
        return """struct user_desc {
    unsigned int  entry_number      = 0x%08x;
    unsigned long base_addr         = 0x%08x;
    unsigned int  limit             = 0x%08x;
    unsigned int  seg_32bit:1       = %u;
    unsigned int  contents:2        = 0x%02x;
    unsigned int  read_exec_only:1  = %u;
    unsigned int  limit_in_pages:1  = %u;
    unsigned int  seg_not_present:1 = %u;
    unsigned int  useable:1         = %u;
};""" % (self.entry_number, self.base_addr, self.limit, self.seg_32bit, self.contents,
         self.read_exec_only, self.limit_in_pages, self.seg_not_present, self.useable)


def sys_set_thread_area(kernel: Kernel):
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
    u_info_addr, = kernel.kernel_args('u')

    logger.info(f'sys_set_thread_area(u_info=0x%08x)', u_info_addr)

    raw_data = kernel.cpu.mem.get_bytes(u_info_addr, sizeof(structUserDesc))

    u_info = structUserDesc.from_buffer_copy(raw_data)

    logger.info('%s', u_info)

    """
    A `user_desc` is considered "empty" if `read_exec_only` and
   `seg_not_present` are set to 1 and all of the other fields are 0.  If
   an "empty" descriptor is passed to `set_thread_area()`, the correspond‐
   ing TLS entry will be cleared.
    """

    selector_index = 0
    if u_info.entry_number == 0xffffffff:  # a.k.a. (unsigned int)(-1)
        """
        When set_thread_area() is passed an entry_number of -1, it searches
        for a free TLS entry.  If set_thread_area() finds a free TLS entry,
        the value of u_info->entry_number is set upon return to show which
        entry was changed.
        """

        from .Registers import SegmentDescriptor
        for selector_index, entry in enumerate(kernel.cpu.GDT[1:], 1):
            seg_descr = SegmentDescriptor.from_buffer_copy(entry)  # segment_descriptor_struct.unpack(entry)

            if seg_descr.P:  # segment present
                continue

            # BEGIN set up BASE
            seg_descr.base_1 = u_info.base_addr & 0xFFFF
            seg_descr.base_2 = (u_info.base_addr >> 16) & 0xFF
            seg_descr.base_3 = (u_info.base_addr >> 24) & 0xFF
            # END set up BASE

            # BEGIN set up LIMIT
            seg_descr.limit_1 = u_info.limit & 0xFFFF
            seg_descr.limit_2 = (u_info.limit >> 16) & 0xF
            # END set up LIMIT

            seg_descr.P = 1  # set segment present to True

            kernel.cpu.GDT[selector_index] = bytes(seg_descr)  # segment_descriptor_struct.pack(*descriptor)

            # print(f'Written segment descriptor: {seg_descr}')

            break

    kernel.cpu.mem.set(u_info_addr, 4, selector_index)  # set address of new selector
    # return success (0) or error (-1)
    return 0


def sys_set_tid_address(kernel: Kernel):
    """
    Arguments: (int *tidptr)

    The system call set_tid_address() sets the clear_child_tid value for
    the calling thread to tidptr.

    :return: always returns the caller's thread ID.
    """

    tidptr, = kernel.kernel_args('u')

    tid = kernel.cpu.mem.get(tidptr, 4)

    logger.info('sys_set_tid_address(tidptr=0x%08x (tid=%d))', tidptr, tid)

    # do nothing, return tid (thread ID)
    return tid


def sys_brk(kernel: Kernel):
    '''
    Arguments: (unsigned long brk)

    https://elixir.bootlin.com/linux/v2.6.35/source/mm/mmap.c#L245
    '''
    brk, = kernel.kernel_args('u')

    logger.info('sys_brk(unsigned long brk = %u)', brk)

    min_brk = kernel.cpu.code_segment_end

    if brk < min_brk:
        logger.info(
            '\tsys_brk: [SUCC] invalid break: 0x%08x < 0x%08x; return 0x%08x',
            brk, min_brk, kernel.cpu.mem.program_break
        )

        return kernel.cpu.mem.program_break

    newbrk = brk
    oldbrk = kernel.cpu.mem.program_break

    if oldbrk == newbrk:
        logger.info('\tsys_brk: [SUCC] not changing break: 0x%08x == 0x%08x', oldbrk, newbrk)

        return kernel.cpu.mem.program_break

    if oldbrk > newbrk:
        # Remove invalid free blocks, if any.
        # A block is invalid if its starting address is greater or equal to the new BRK.
        cutoff = len(kernel.free_memory_blocks)
        for cutoff in range(cutoff - 1, -1, -1):
            s, e = kernel.free_memory_blocks[cutoff]

            if s < newbrk <= e:
                kernel.free_memory_blocks[cutoff] = s, newbrk
                cutoff -= 1
                break

        # `kernel.free_memory_blocks` is sorted, so `cutoff` chops off the invalid blocks
        kernel.free_memory_blocks = kernel.free_memory_blocks[:cutoff]

    kernel.cpu.mem.program_break = brk

    logger.info(
        '\tsys_brk: [SUCC] changing break: 0x%08x -> 0x%08x (%+d bytes)',
        oldbrk, kernel.cpu.mem.program_break, kernel.cpu.mem.program_break - oldbrk
    )

    return kernel.cpu.mem.program_break


def sys_mmap(kernel: Kernel):
    """
    void *mmap2(void *addr, size_t length, int prot, int flags,
              int fd, off_t offset);

    See: http://www.man7.org/linux/man-pages/man2/mmap2.2.html
    """

    import enum

    class MAP_FLAGS(enum.Flag):
        # see http://people.seas.harvard.edu/~apw/sreplay/src/linux/mmap.c
        MAP_SHARED    = 0x01   # Share changes
        MAP_PRIVATE   = 0x02   # Changes are private.
        MAP_FIXED     = 0x10   # Interpret addr exactly.
        MAP_FILE      = 0
        MAP_ANONYMOUS = 0x20   # Don't use a file.

    class MAP_PROT(enum.Flag):
        # see above
        PROT_READ  = 0x1  # Page can be read.
        PROT_WRITE = 0x2  # Page can be written.
        PROT_EXEC  = 0x4  # Page can be executed.
        PROT_NONE  = 0x0  # Page can not be accessed.

    addr, length, prot, flags, fd = kernel.kernel_args('uusss')

    flags = MAP_FLAGS(flags)
    prot = MAP_PROT(prot)

    logger.info(
        'mmap(void *addr=0x%08x, size_t length=%d, int prot=%s, int flags=%s, int fd=%d, off_t offset=%d)',
        addr, length, str(prot), str(flags), fd, -1
    )

    if flags & MAP_FLAGS.MAP_ANONYMOUS:
        # TODO: Do something with protection?

        for i, (start, end) in enumerate(kernel.free_memory_blocks):
            assert end >= start

            if end - start == length:
                kernel.free_memory_blocks.pop(i)

                logger.info('\tmmap: [SUCC] found exactly %d bytes of free space', length)
                return kernel.cpu.mem.memset(start, 0, length)

            if end - start > length:
                _end = start + length
                kernel.free_memory_blocks[i] = _end, end

                logger.info('\tmmap: [SUCC] found more than %d bytes of free space', length)

                return kernel.cpu.mem.memset(start, 0, length)

        old_brk = kernel.cpu.mem.memset(kernel.cpu.mem.program_break, 0, length)
        kernel.cpu.mem.program_break += length

        logger.info('\tmmap: [SUCC] allocated %d bytes', length)

        return old_brk

    logger.error('\tmmap: [ERR] unknown flags: %s', flags)

    return -1


def _munmap_fuse_memory_blocks(kernel: Kernel):
    kernel.free_memory_blocks.sort()

    did_fuse = True

    while did_fuse:
        did_fuse = False

        for i in range(len(kernel.free_memory_blocks) - 1):
            fst, snd = kernel.free_memory_blocks[i], kernel.free_memory_blocks[i + 1]

            if fst[0] <= snd[0] and snd[1] <= fst[1]:  # snd contained in fst
                kernel.free_memory_blocks[i] = None
                kernel.free_memory_blocks[i + 1] = fst
                did_fuse = True
            elif fst[0] <= snd[0] <= fst[1] < snd[1]:  # fst intersects snd
                kernel.free_memory_blocks[i] = None
                kernel.free_memory_blocks[i + 1] = fst[0], snd[1]
                did_fuse = True

        if did_fuse:
            kernel.free_blocks = sorted(filter(None, kernel.free_memory_blocks))


def sys_munmap(kernel: Kernel):
    """
    int munmap(void *addr, size_t length);
    """

    addr, length = kernel.kernel_args('uu')

    logger.info('sys_munmap(void *addr = 0x%08x, size_t length = %u)', addr, length)

    s, e = addr, addr + length

    if e == kernel.cpu.mem.program_break:
        kernel.cpu.mem.program_break -= length

        logger.info(
            'munmap: [SUCC] unmapping %d bytes at 0x%08x at the end of mapped area',
            length, addr
        )
    else:
        kernel.free_memory_blocks.append((s, e))
        _munmap_fuse_memory_blocks(kernel)

        logger.info(
            'munmap: [SUCC] unmapping %d bytes at 0x%08x inside mapped area',
            length, addr
        )

    if kernel.free_memory_blocks and kernel.free_memory_blocks[-1][1] >= kernel.cpu.mem.program_break:
        kernel.cpu.mem.program_break = kernel.free_memory_blocks[-1][0]
        kernel.free_memory_blocks.pop()

    logger.info('munmap: [SUCC] unmapped %d bytes at 0x%08x', length, addr)

    return 0


Kernel.register(sys_set_thread_area, 0xf3)
Kernel.register(sys_set_tid_address, 0x102)
Kernel.register(sys_brk, 0x2d)
Kernel.register(sys_mmap, 0xc0)
Kernel.register(sys_munmap, 0x5b)
