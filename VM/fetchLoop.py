from .debug import debug


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


def execute_bytes(self, data: bytes, offset=0):
    self.mem.set(offset, data)
    self.code_segment_end = offset + len(data) - 1
    self.eip = offset
    self.run()


def execute_file(self, fname: str, offset=0):
    with open(fname, 'rb') as f:
        data = f.read()
        self.mem.set(offset, data)

    self.code_segment_end = offset + len(data) - 1
    self.eip = offset
    self.run()
