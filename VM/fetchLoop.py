from .debug import debug


def execute_opcode(self, op: int) -> None:
    """
    Attempts to execute the current opcode `op`. The calls to `_<mnemonic name>` check whether the opcode corresponds to
    a mnemonic. This basically checks whether the opcode is supported and executes it if so.
    :param self: passed implicitly
    :param op: the current opcode
    :return: None
    """
    debug(self.fmt.format(self.eip, op))
    self.eip += 1  # points to next data

    if op == 0x90:  # nop
        return
        
    for instruction in self.instr:
    	if instruction(op):
    		debug('{} success'.format(instruction.__name__[1:]))
    		return
    else:
    	raise ValueError('Unknown opcode: 0x{:02x}'.format(op))
    


def override(self, name: str):
    if not name:
        return

    old_size = getattr(self, name)
    self.current_mode = not self.current_mode
    setattr(self, name, self.sizes[self.current_mode])
    debug('{} override ({} -> {})'.format(name, old_size, self.operand_size))

def run(self):
    """
    Implements the basic CPU instruction cycle (https://en.wikipedia.org/wiki/Instruction_cycle)
    :param self: passed implicitly
    :param offset: location of the first opcode
    :return: None
    """

    self.load_instructions()
    self.running = True

    while self.running and self.eip + 1 in self.mem.bounds:
        override_name = ''
        opcode = self.mem.get(self.eip, 1)[0]

        if opcode == 0x66:
            override_name = 'operand_size'

            self.override(override_name)

            self.eip += 1
            opcode = self.mem.get(self.eip, 1)[0]
        elif opcode == 0x67:
            override_name = 'address_size'

            self.override(override_name)

            self.eip += 1
            opcode = self.mem.get(self.eip, 1)[0]

        self.execute_opcode(opcode)

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
