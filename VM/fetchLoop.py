import enum

from .ELF import ELF32, enums
from .util import SegmentRegs, MissingOpcodeError
from .CPU import CPU32

import logging
logger = logging.getLogger(__name__)


class FetchLoopMixin:
    _attrs_ = 'eip', 'mem', 'reg.ebx', 'fmt', 'instr', 'sizes', 'default_mode'

    def execute_opcode(self: CPU32) -> None:
        self.eip += 1

        off = 1
        if self.opcode == 0x0F:
            op = self.mem.get_eip(self.eip, 1)
            self.eip += 1

            self.opcode = (self.opcode << 8) | op
            off += 1

        if __debug__:
            logger.debug(self.fmt, self.eip - off, self.opcode)

        try:
            impls = self.instr[self.opcode]
        except KeyError:
            ...  # could not find opcode
        else:
            for impl in impls:
                if impl():
                    return  # opcode executed
            # could not find suitable implementation

        # read one more byte
        op = self.mem.get_eip(self.eip, 1)
        self.eip += 1

        self.opcode = (self.opcode << 8) | op

        try:
            impls = self.instr[self.opcode]
        except KeyError:
            raise MissingOpcodeError(f'Opcode {self.opcode:x} is not recognized yet (at 0x{self.eip - off - 1:08x})')
        else:
            for impl in impls:
                if impl():
                    return  # opcode executed
            # could not find suitable implementation

        raise NotImplementedError(f'No suitable implementation found for opcode {self.opcode:x} (@0x{self.eip - off - 1:02x})')

    def run(self: CPU32) -> int:
        """
        Implements the basic CPU instruction cycle (https://en.wikipedia.org/wiki/Instruction_cycle)
        :param self: passed implicitly
        :param offset: location of the first opcode
        :return: None
        """

        # opcode perfixes
        pref_segments = {
            0x2E: SegmentRegs.CS,
            0x36: SegmentRegs.SS,
            0x3E: SegmentRegs.DS,
            0x26: SegmentRegs.ES,
            0x64: SegmentRegs.FS,
            0x65: SegmentRegs.GS
        }
        pref_op_size_override = {0x66, 0x67}
        pref_lock = {0xf0}
        rep = {0xf3}

        prefixes = set(pref_segments) | pref_op_size_override | pref_lock | rep
        self.running = True

        while self.running and self.eip + 1 < self.mem.size:
            overrides = []
            self.opcode = self.mem.get(self.eip, 1)

            while self.opcode in prefixes:
                overrides.append(self.opcode)
                self.eip += 1
                self.opcode = self.mem.get(self.eip, 1)

            # apply overrides
            size_override_active = False
            for ov in overrides:
                if ov == 0x66:
                    if not size_override_active:
                        self.current_mode = not self.current_mode
                        size_override_active = True
                    old_operand_size = self.operand_size
                    self.operand_size = self.sizes[self.current_mode]
                    logger.debug(
                        'Operand size override: %d -> %d',
                        old_operand_size, self.operand_size
                    )
                elif ov == 0x67:
                    if not size_override_active:
                        self.current_mode = not self.current_mode
                        size_override_active = True
                    old_address_size = self.address_size
                    self.address_size = self.sizes[self.current_mode]
                    logger.debug(
                        'Address size override: %d -> %d',
                        old_address_size, self.address_size
                    )
                elif ov in pref_segments:
                    is_special = ov >> 6
                    if is_special:
                        sreg_number = 4 + (ov & 1)  # FS or GS
                    else:
                        sreg_number = (ov >> 3) & 0b11
                    self.mem.segment_override = sreg_number
                    logger.debug('Segment override: %s', self.mem.segment_override)
                elif ov == 0xf0:  # LOCK prefix
                    logger.debug('LOCK prefix')  # do nothing; all operations are atomic anyway. Right?
                elif ov == 0xf3:  # REP prefix
                    self.opcode = ov
                    self.eip -= 1  # repeat the previous opcode

            self.execute_opcode()

            # undo all overrides
            for ov in overrides:
                if ov == 0x66:
                    self.current_mode = self.default_mode
                    self.operand_size = self.sizes[self.current_mode]
                elif ov == 0x67:
                    self.current_mode = self.default_mode
                    self.address_size = self.sizes[self.current_mode]
                elif ov in pref_segments:
                    self.mem.segment_override = SegmentRegs.DS

        return self.reg.eax


class ExecutionStrategy(enum.Enum):
    BYTES = 1
    FLAT = 2
    ELF = 3


class ExecutionMixin(FetchLoopMixin):
    def execute(self, *args, **kwargs):
        return NotImplemented


class ExecuteBytes(ExecutionMixin):
    _attrs_ = 'eip', 'mem', 'code_segment_end'
    _funcs_ = 'run',

    def execute(self: CPU32, data: bytes, offset=0):
        l = len(data)
        self.mem.set_bytes(offset, l, data)

        self.eip = offset
        self.code_segment_end = self.eip + l - 1
        self.mem.program_break = self.code_segment_end

        return self.run()


class ExecuteFlat(ExecutionMixin):
    _attrs_ = 'eip', 'mem', 'code_segment_end'
    _funcs_ = 'run',

    def execute(self: CPU32, fname: str, offset=0):
        with open(fname, 'rb') as f:
            data = f.read()
            l = len(data)
            self.mem.set_bytes(offset, l, data)

        self.eip = offset
        self.code_segment_end = self.eip + l - 1
        self.mem.program_break = self.code_segment_end

        return self.run()
    

class ExecuteELF(ExecutionMixin):
    _attrs_ = 'eip', 'mem', 'reg', 'code_segment_end'
    _funcs_ = 'run', 'stack_init', 'stack_push'

    def execute(self: CPU32, fname: str, args=()):
        with ELF32(fname) as elf:
            if elf.hdr.e_type != enums.e_type.ET_EXEC:
                raise ValueError(f'ELF file {elf.fname!r} is not executable (type: {elf.hdr.e_type})')

            max_memsz = max(
                phdr.p_vaddr + phdr.p_memsz
                for phdr in elf.phdrs
                if phdr.p_type == enums.p_type.PT_LOAD
            )

            if self.mem.size < max_memsz * 2:
                self.mem.size = max_memsz * 2
                self.stack_init()

            for phdr in elf.phdrs:
                if phdr.p_type not in (enums.p_type.PT_LOAD, enums.p_type.PT_GNU_EH_FRAME):
                    continue

                logger.info(f'LOAD {phdr.p_memsz:10,d} bytes at address 0x{phdr.p_vaddr:09_x}')
                elf.file.seek(phdr.p_offset)

                data = elf.file.read(phdr.p_filesz)
                self.mem.set_bytes(phdr.p_vaddr, len(data), data)
                self.mem.set_bytes(phdr.p_vaddr + phdr.p_filesz, phdr.p_memsz - phdr.p_filesz, bytearray(phdr.p_memsz - phdr.p_filesz))

        self.eip = elf.hdr.e_entry
        self.code_segment_end = self.eip + max_memsz - 1
        self.mem.program_break = self.code_segment_end

        # INITIALIZE STACK LAYOUT:
        #   http://asm.sourceforge.net/articles/startup.html
        #   https://lwn.net/Articles/631631/

        environment = ["USER=ForceBru"]
        args = [fname] + list(args)

        arg_addresses, env_addresses = [], []
        for arg in args:
            arg = arg.encode() + b'\0'
            l = len(arg)
            self.mem.set_bytes(self.reg.esp - l, l, arg)
            self.reg.esp -= l
            arg_addresses.append(self.reg.esp)

        for env in environment:
            env = env.encode() + b'\0'
            l = len(env)
            self.mem.set_bytes(self.reg.esp - l, l, env)
            self.reg.esp -= l
            env_addresses.append(self.reg.esp)

        # auxiliary vector (just NULL)
        self.stack_push(0)

        # environment (array of pointers + NULL)
        self.stack_push(0)
        for addr in env_addresses[::-1]:
            self.stack_push(addr)

        # argv
        self.stack_push(0)  # end of argv
        for addr in arg_addresses[::-1]:
            self.stack_push(addr)

        # argc
        self.stack_push(len(args))

        logger.info(f'EXEC at 0x{self.eip:09_x}')
        # logger.debug(f'Stack start at 0x{self.reg.esp:08x}')
        # logger.debug(f'Stack end at 0x{self.reg.ebp:08x}')

        return self.run()
