from .debug import debug
from .util import byteorder

from .ELF import ELF32, enums


def execute_opcode(self) -> None:
    """
    Attempts to execute the current opcode `op`. The calls to `_<mnemonic name>` check whether the opcode corresponds to
    a mnemonic. This basically checks whether the opcode is supported and executes it if so.
    :param self: passed implicitly
    :param op: the current opcode
    :return: None
    """
    self.eip += 1  # points to next data

    if self.opcode == 0x90:  # nop
        if debug: print(self.fmt.format(self.eip - 1, self.opcode))
        return

    opcode = self.opcode
    if opcode == 0x0F:  # handle prefix
        op = self.mem.get(self.eip, 1)[0]  # 0xYY
        self.eip += 1

        opcode = (opcode << 8) + op  # opcode <- 0x0FYY
        self.opcode = op

        if debug: print(self.fmt.format(self.eip - 2, opcode))
    else:
        if debug: print(self.fmt.format(self.eip - 1, opcode))
     
    try:   
        for instruction in self.instr[opcode]:
            if instruction():
                return

        # TODO: this is a mess
        # Try to interpret two-byte instruction
        op = self.mem.get(self.eip, 1)[0]  # 0xYY
        self.eip += 1

        opcode = (opcode << 8) + op  # opcode <- 0x0FYY
        self.opcode = op

        if debug: print(self.fmt.format(self.eip - 2, opcode))

        try:
            for instruction in self.instr[opcode]:
                if instruction():
                    return
        except KeyError:
            raise RuntimeError(f'Opcode 0x{opcode:02x} is not implemented yet (@0x{self.eip:02x})')
    except KeyError:
        # TODO: this is a mess as well
        # Try to interpret two-byte instruction
        op = self.mem.get(self.eip, 1)[0]  # 0xYY
        self.eip += 1

        opcode = (opcode << 8) + op  # opcode <- 0x0FYY
        self.opcode = op

        if debug: print(self.fmt.format(self.eip - 2, opcode))

        try:
            for instruction in self.instr[opcode]:
                if instruction():
                    return
        except KeyError:
            raise RuntimeError(f'Opcode 0x{opcode:02x} is not implemented yet (@0x{self.eip:02x})')

        raise ValueError(f'Unknown opcode: 0x{opcode:02x}')
    

def override(self, name: str):
    if not name:
        return

    old_size = getattr(self, name)
    self.current_mode = not self.current_mode
    setattr(self, name, self.sizes[self.current_mode])
    if debug: print('{} override ({} -> {})'.format(name, old_size, self.operand_size))


def run(self):
    """
    Implements the basic CPU instruction cycle (https://en.wikipedia.org/wiki/Instruction_cycle)
    :param self: passed implicitly
    :param offset: location of the first opcode
    :return: None
    """

    self.running = True

    while self.running and self.eip + 1 in self.mem.bounds:
        override_name = ''
        self.opcode = self.mem.get(self.eip, 1)[0]

        if self.opcode == 0x66:
            override_name = 'operand_size'

            self.override(override_name)

            self.eip += 1
            self.opcode = self.mem.get(self.eip, 1)[0]
        elif self.opcode == 0x67:
            override_name = 'address_size'

            self.override(override_name)

            self.eip += 1
            self.opcode = self.mem.get(self.eip, 1)[0]

        self.execute_opcode()

        self.override(override_name)

    ebx = int.from_bytes(self.reg.get(3, 4), byteorder)
    return ebx


def execute_bytes(self, data: bytes, offset=0):
    self.mem.set(offset, data)

    self.eip = offset
    self.code_segment_end = self.eip + len(data) - 1
    self.mem.program_break = self.code_segment_end
    
    return self.run()


def execute_file(self, fname: str, offset=0):
    with open(fname, 'rb') as f:
        data = f.read()
        self.mem.set(offset, data)

    self.eip = offset
    self.code_segment_end = self.eip + len(data) - 1
    self.mem.program_break = self.code_segment_end
    
    return self.run()
    
    
def execute_elf(self, fname: str, args=tuple()):
    with ELF32(fname) as elf:
        if elf.hdr.e_type != enums.e_type.ET_EXEC:
            raise ValueError(f'ELF file {elf.fname!r} is not executable (type: {elf.hdr.e_type})')
            
        max_memsz = max(
            phdr.p_vaddr + phdr.p_memsz
            for phdr in elf.phdrs
            if phdr.p_type == enums.p_type.PT_LOAD
        )

        if self.mem.size < max_memsz * 2:
            self.mem.size_set(max_memsz * 2)
            self.stack_init()
        
        for phdr in elf.phdrs:
            if phdr.p_type != enums.p_type.PT_LOAD:
                continue
                
            print(f'LOAD {phdr.p_memsz:10,d} bytes at address 0x{phdr.p_vaddr:09_x}')
            elf.file.seek(phdr.p_offset)
            
            self.mem.set(phdr.p_vaddr, elf.file.read(phdr.p_filesz))            
            self.mem.set(phdr.p_vaddr + phdr.p_filesz, bytearray(phdr.p_memsz - phdr.p_filesz))
    
    self.eip = elf.hdr.e_entry
    self.code_segment_end = self.eip + max_memsz - 1
    self.mem.program_break = self.code_segment_end

    # INITIALIZE STACK LAYOUT (http://asm.sourceforge.net/articles/startup.html)
    # push program name:
    PROG_NAME = b'tes\0'
    ARG_COUNT = 0
    self.stack_push(PROG_NAME)

    # push command-line arguments:
    self.stack_push((0).to_bytes(4, byteorder))  # NULL - end of environment
    # no envirenment here
    self.stack_push((0).to_bytes(4, byteorder))  # NULL - end of arguments
    # no arguments here
    self.stack_push((self.mem.size - 1 - len(PROG_NAME)).to_bytes(4, byteorder))  # pointer to program name
    self.stack_push(ARG_COUNT.to_bytes(4, byteorder))
    
    print(f'EXEC at 0x{self.eip:09_x}')
    
    return self.run()
