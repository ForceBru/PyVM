from .debug import debug


def execute_opcode(self, op: int):
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
    elif self._mov(op):
        debug('mov success')
    elif self._jmp(op):
        debug('jmp success')
    elif self._int(op):
        debug('int success')
    elif self._push(op):
        debug('push success')
    elif self._pop(op):
        debug('pop success')
    elif self._call(op):
        debug('call success')
    elif self._ret(op):
        debug('ret success')
    elif self._add(op):
        debug('add success')
    elif self._sub(op):
        debug('sub success')
    else:
        raise ValueError('Unknown opcode: "{}"'.format(hex(op)))


def run(self, offset=0):
    """
    Implements the basic CPU instruction cycle (https://en.wikipedia.org/wiki/Instruction_cycle)
    :param self: passed implicitly
    :param offset: location of the first opcode
    :return: None
    """
    assert offset in self.mem.bounds

    self.eip = offset
    self.running = True

    while self.running and self.eip + 1 in self.mem.bounds:
        opcode = self.mem.get(self.eip, 1)[0]

        if opcode == 0x66:
            self.current_mode = not self.current_mode
            debug('Mode switch begin -> {}'.format(self.modes[self.current_mode]))

            self.eip += 1
            opcode = self.mem.get(self.eip, 1)[0]
            self.execute_opcode(opcode)

            self.current_mode = not self.current_mode
            debug('Mode switch end -> {}'.format(self.modes[self.current_mode]))
        else:
            self.execute_opcode(opcode)


def execute_file(self, fname: str):
    with open(fname, 'rb') as f:
        self.mem.set(0, f.read())

    self.run()
