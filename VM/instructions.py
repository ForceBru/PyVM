import operator
from .debug import debug
from .misc import sign_extend, parity
from .CPU import to_int, byteorder
from .Registers import Reg32

'''
These are the implementations of various instructions grouped in a submodule to avoid code duplication.
These functions are only to be called from `__init__.py`.

Each function should be named based on the following scheme:
    <mnemonic>_<arg1>_<arg2>

Each block of functions (i.e., functions implementing the same instruction) should be preceded by a comment in the form:
    ####################
    # <INSTRUCTION MNEMONIC>[ / <another INSTRUCTION MNEMONIC>]*
    ####################
'''

####################
# MOV
####################
def mov_r_imm(self, off, op) -> None:
    """
    Move data from one location (a) to another (b).

    Flags:
        None affected

    Operation: b <- a
    """
    imm = self.mem.get(self.eip, off)
    self.eip += off

    r = op & 0b111
    self.reg.set(r, imm)
    debug('mov r{0}({1}),imm{0}({2})'.format(off * 8, r, imm))


def mov_rm_imm(self, off) -> bool:
    """
    [See `mov_r_imm` for description].
    """
    RM, R = self.process_ModRM(off, off)
    if R[1] != 0:
        return False
    type, loc, _ = RM

    imm = self.mem.get(self.eip, off)
    self.eip += off

    (self.mem if type else self.reg).set(loc, imm)
    debug('mov {0}{1}({2}),imm{1}({3})'.format(('m' if type else '_r'), off * 8, loc, imm))

    return True


def mov_rm_r(self, off) -> None:
    """
    [See `mov_r_imm` for description].
    """
    RM, R = self.process_ModRM(off, off)

    type, loc, _ = RM

    data = self.reg.get(R[1], R[2])

    (self.mem if type else self.reg).set(loc, data)
    debug('mov {0}{1}({2}),r{1}({3})'.format(('m' if type else '_r'), off * 8, loc, data))


def mov_r_rm(self, off) -> None:
    """
    [See `mov_r_imm` for description].
    """
    RM, R = self.process_ModRM(off, off)

    type, loc, sz = RM

    data = (self.mem if type else self.reg).get(loc, sz)
    self.reg.set(R[1], data)

    debug('mov r{1}({2}),{0}{1}({3})'.format(('m' if type else '_r'), off * 8, R[1], data))


def mov_eax_moffs(self, off) -> None:
    """
    [See `mov_r_imm` for description].
    """
    loc = to_int(self.mem.get(self.eip, self.address_size))
    self.eip += self.address_size

    data = self.mem.get(loc, off)
    self.reg.set(0, data)
    debug('mov {}, moffs{}({}:{})'.format({1: 'al', 2: 'ax', 4: 'eax'}[off], off * 8, loc, data))


def mov_moffs_eax(self, off) -> None:
    """
    [See `mov_r_imm` for description].
    """
    loc = to_int(self.mem.get(self.eip, self.address_size))
    self.eip += self.address_size

    data = self.reg.get(0, off)
    self.mem.set(loc, data)
    debug('mov moffs{}({}), {}({})'.format(off * 8, loc, {1: 'al', 2: 'ax', 4: 'eax'}[off], data))


MAXVALS = [None, (1 << 8) - 1, (1 << 16) - 1, None, (1 << 32) - 1]
SIGNS   = [None, 1 << 8 - 1, 1 << 16 - 1, None, 1 << 32 - 1]

####################
# JMP
####################	
def jmp_rel(self, off) -> None:
    """
    Jump to a memory address.

    Operation:
        EIP = memory_location
    """
    d = self.mem.get(self.eip, off)
    d = to_int(d, True)
    self.eip += off + d
    
    assert self.eip in self.mem.bounds
    
    debug('jmp rel{}({})'.format(off * 8, hex(self.eip)))


def jmp_rm(self, off) -> bool:
    """
    [See `jmp_rel` for description].
    """
    old_eip = self.eip

    RM, R = self.process_ModRM(off, off)

    if R[1] != 4:
        self.eip = old_eip
        return False  # this is not JMP rm

    disp = self.mem.get(self.eip, off)
    self.eip = to_int(disp) & MAXVALS[off]

    assert self.eip in self.mem.bounds

    debug('jmp rm{}({})'.format(off * 8, self.eip))

    return True


def jmp_m(self, off) -> bool:
    """
    [See `jmp_rel` for description].
    """
    old_eip = self.eip

    RM, R = self.process_ModRM(off, off)

    if R[1] != 5:
        self.eip = old_eip
        return False  # this is not JMP m

    addr = to_int(self.mem.get(self.eip, self.address_size))
    disp = self.mem.get(addr, off)
    self.eip = to_int(disp) & MAXVALS[off]

    assert self.eip in self.mem.bounds

    debug('jmp m{}({})'.format(off * 8, self.eip))

    return True


####################
# INT
####################
def int_3(self, off) -> None:
    self.descriptors[2].write("[!] It's a trap! (literally)")


def int_imm(self, off) -> None:
    """
    Call to interrupt procedure.
    """
    imm = self.mem.get(self.eip, off)
    imm = to_int(imm)
    self.eip += off

    self.interrupt(imm)


####################
# PUSH
####################
def push_rm(self, off) -> bool:
    """
    Push data onto the stack.
    """
    old_eip = self.eip

    RM, R = self.process_ModRM(off, off)

    if R[1] != 6:
        self.eip = old_eip
        return False  # this is not PUSH rm

    type, loc, _ = RM

    data = (self.mem if type else self.reg).get(loc, off)
    self.stack_push(data)

    debug('push {2}{0}({1})'.format(off * 8, data, ('m' if type else '_r')))
    return True


def push_imm(self, off) -> None:
    """
    [See `push_rm` for description].
    """
    data = self.mem.get(self.eip, off)
    self.eip += off

    self.stack_push(data)

    debug('push imm{}({})'.format(off * 8, data))


def push_sreg(self, reg: str) -> None:
    """
    Push a segment register onto the stack.

    :param reg: the name of the register to be pushed.
    """

    self.stack_push(getattr(self.reg, reg).to_bytes(2, byteorder))
    debug('push {}'.format(reg))


####################
# POP
####################
def pop_rm(self, off) -> bool:
    """
    Pop data from the stack.
    """
    old_eip = self.eip

    RM, R = self.process_ModRM(off, off)

    if R[1] != 0:
        self.eip = old_eip
        return False  # this is not POP rm

    type, loc, _ = RM

    data = self.stack_pop(off)

    (self.mem if type else self.reg).set(loc, data)

    debug('pop {2}{0}({1})'.format(off * 8, data, ('m' if type else '_r')))

    return True


def pop_sreg(self, reg: str, sz: int) -> None:
    data = self.stack_pop(sz)

    setattr(self.reg, reg, to_int(data, False))
    debug('pop {}'.format(reg))


####################
# CALL
####################
def call_rel(self, off) -> None:
    """
    Call a procedure.
    """
    dest = self.mem.get(self.eip, off)
    self.eip += off
    dest = to_int(dest, True)
    tmpEIP = self.eip + dest

    assert tmpEIP in self.mem.bounds

    self.stack_push(self.eip.to_bytes(off, byteorder, signed=True))
    self.eip = tmpEIP

    debug("call rel{}({})".format(off * 8, self.eip))


def call_rm(self, off) -> bool:
    """
    [See `call_rel` for description].
    """
    old_eip = self.eip

    RM, R = self.process_ModRM(off, off)

    if R[1] != 2:
        self.eip = old_eip
        return False  # this is not CALL rm

    type, loc, _ = RM

    dest = (self.mem if type else self.reg).get(loc, off)

    tmpEIP = to_int(dest, False) & MAXVALS[off]
    self.stack_push(self.eip.to_bytes(off, byteorder, signed=False))

    self.eip = tmpEIP
    debug("call {2}{0}({1})".format(off * 8, self.eip, 'rm'[type]))

    return True


def call_m(self, off) -> bool:
    """
    [See `call_rel` for description].
    """
    old_eip = self.eip

    RM, R = self.process_ModRM(off, off)

    if R[1] != 3:
        self.eip = old_eip
        return False  # this is not CALL m

    type, loc, _ = RM

    addr = to_int((self.mem if type else self.reg).get(self.eip, self.address_size))
    dest = self.mem.get(addr, off)

    tmpEIP = to_int(dest, False) & MAXVALS[off]
    self.stack_push(self.eip.to_bytes(off, byteorder, signed=False))

    self.eip = tmpEIP
    debug("call {2}{0}({1})".format(off * 8, self.eip, 'rm'[type]))

    return True


####################
# RET
####################
def ret_near(self, off) -> None:
    """
    Return to calling procedure.
    """
    self.eip = to_int(self.stack_pop(off), True)

    debug("ret ({})".format(self.eip))


def ret_near_imm(self, off) -> None:
    """
    [See `ret_near` for description].
    """
    self.eip = to_int(self.stack_pop(off), True)

    imm = to_int(self.mem.get(self.eip, off))
    self.eip += off

    self.stack_pop(imm)

    debug("ret ({})".format(self.eip))


def ret_far(self, off) -> None:
    """
    [See `ret_near` for description].
    """
    raise RuntimeError("far returns not implemented yet")
    self.eip = to_int(self.stack_pop(off), True)
    # self.reg.CS = to_int(self.stack_pop(off), True)  and discard high-order 16 bits if necessary


def ret_far_imm(self, off) -> None:
    """
    [See `ret_near` for description].
    """
    raise RuntimeError("far returns (imm) not implemented yet")
    # the same as above, but adjust SP

####################
# ADD / SUB / CMP / ADC / SBB
####################
def addsub_al_imm(self, off, sub=False, cmp=False, carry=False) -> None:
    """
    Perform addition or subtraction.
    Flags:
        OF, SF, ZF, AF, CF, and PF flags are set according to the result.

    Operation: c <- a [op] b

    :param sub: indicates whether the instruction to be executed is SUB. If False, ADD is executed.
    :param cmp: indicates whether the instruction to be executed is CMP.
    :param carry: indicates whether the instruction to be executed is ADC or SBB. Must be combined with the `sub` parameter.
    """
    b = self.mem.get(self.eip, off)
    self.eip += off
    b = to_int(b)

    if carry:
        b += self.reg.eflags_get(Reg32.CF)

    a = to_int(self.reg.get(0, off))

    c = a + (b if not sub else MAXVALS[off] + 1 - b)
    
    sign_a = (a >> (off * 8 - 1)) & 1
    sign_b = (b >> (off * 8 - 1)) & 1
    sign_c = (c >> (off * 8 - 1)) & 1
    
    if not sub:
        self.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.CF, c > MAXVALS[off])
        self.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
    else:
        self.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.CF, b > a)
        self.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))
        
    self.reg.eflags_set(Reg32.SF, sign_c)

    c &= MAXVALS[off]

    self.reg.eflags_set(Reg32.ZF, c == 0)

    c = c.to_bytes(off, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], off))
    
    if not cmp:
        self.reg.set(0, c)

    name = 'sub' if sub else 'add'
    debug('{} {}, imm{}({})'.format('cmp' if cmp else name, [0, 'al', 'ax', 0, 'eax'][off], off * 8, b))


def addsub_rm_imm(self, off, imm_sz, sub=False, cmp=False, carry=False) -> bool:
    """
    [See `addsub_al_imm` for description].
    """
    assert off >= imm_sz
    old_eip = self.eip

    RM, R = self.process_ModRM(off, off)

    if not sub:
        if (not carry) and (R[1] != 0):
            self.eip = old_eip
            return False  # this is not ADD
        elif carry and (R[1] != 2):
            self.eip = old_eip
            return False  # this is not ADC
    elif sub:
        if not carry:
            if not cmp and (R[1] != 5):
                self.eip = old_eip
                return False  # this is not SUB
            elif cmp and (R[1] != 7):
                self.eip = old_eip
                return False  # this is not CMP
        else:
            if R[1] != 3:
                self.eip = old_eip
                return False  # this is not SBB

    b = self.mem.get(self.eip, imm_sz)
    self.eip += imm_sz
    b = sign_extend(b, off)
    b = to_int(b)

    if carry:
        b += self.reg.eflags_get(Reg32.CF)
    
    type, loc, _ = RM

    a = to_int((self.mem if type else self.reg).get(loc, off))
    c = a + (b if not sub else MAXVALS[off] + 1 - b)
    
    sign_a = (a >> (off * 8 - 1)) & 1
    sign_b = (b >> (off * 8 - 1)) & 1
    sign_c = (c >> (off * 8 - 1)) & 1
    
    if not sub:
        self.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.CF, c > MAXVALS[off])
        self.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
    else:
        self.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.CF, b > a)
        self.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))
        
    self.reg.eflags_set(Reg32.SF, sign_c)

    c &= MAXVALS[off]

    self.reg.eflags_set(Reg32.ZF, c == 0)
    
    c = c.to_bytes(off, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], off))

    if not cmp:
        (self.mem if type else self.reg).set(loc, c)

    name = 'sub' if sub else 'add'
    debug('{0} {5}{1}({2}),imm{3}({4})'.format('cmp' if cmp else name, off * 8, loc, imm_sz * 8, b, ('m' if type else 'r')))

    return True


def addsub_rm_r(self, off, sub=False, cmp=False, carry=False) -> None:
    """
    [See `addsub_al_imm` for description].
    """
    RM, R = self.process_ModRM(off, off)

    type, loc, _ = RM

    a = to_int((self.mem if type else self.reg).get(loc, off))
    b = to_int(self.reg.get(R[1], off))

    if carry:
        b += self.reg.eflags_get(Reg32.CF)

    c = a + (b if not sub else MAXVALS[off] + 1 - b)

    sign_a = (a >> (off * 8 - 1)) & 1
    sign_b = (b >> (off * 8 - 1)) & 1
    sign_c = (c >> (off * 8 - 1)) & 1
    
    if not sub:
        self.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.CF, c > MAXVALS[off])
        self.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
    else:
        self.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.CF, b > a)
        self.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))
        
    self.reg.eflags_set(Reg32.SF, sign_c)

    c &= MAXVALS[off]

    self.reg.eflags_set(Reg32.ZF, c == 0)
    
    c = c.to_bytes(off, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], off))

    if not cmp:
        (self.mem if type else self.reg).set(loc, c)

    name = 'sub' if sub else 'add'
    debug('{0} {4}{1}({2}),r{1}({3})'.format('cmp' if cmp else name, off * 8, loc, R[1], ('m' if type else '_r')))


def addsub_r_rm(self, off, sub=False, cmp=False, carry=False) -> None:
    """
    [See `addsub_al_imm` for description].
    """
    RM, R = self.process_ModRM(off, off)

    type, loc, _ = RM

    a = to_int((self.mem if type else self.reg).get(loc, off))
    b = to_int(self.reg.get(R[1], off))

    if carry:
        b += self.reg.eflags_get(Reg32.CF)

    c = a + (b if not sub else MAXVALS[off] + 1 - b)

    sign_a = (a >> (off * 8 - 1)) & 1
    sign_b = (b >> (off * 8 - 1)) & 1
    sign_c = (c >> (off * 8 - 1)) & 1
    
    if not sub:
        self.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.CF, c > MAXVALS[off])
        self.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
    else:
        self.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.CF, b > a)
        self.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))
        
    self.reg.eflags_set(Reg32.SF, sign_c)

    c &= MAXVALS[off]

    self.reg.eflags_set(Reg32.ZF, c == 0)
    
    c = c.to_bytes(off, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], off))

    if not cmp:
        self.reg.set(R[1], c)

    name = 'sub' if sub else 'add'
    debug('{0} r{1}({2}),{4}{1}({3})'.format('cmp' if cmp else name, off * 8, R[1], loc, ('m' if type else '_r')))


####################
# AND / OR / XOR / TEST
####################
def bitwise_al_imm(self, off, operation, test=False) -> None:
    """
    Perform a bitwise operation.
    Flags:
        OF, CF cleared
        SF, ZF, PF set according to the result
        AF undefined

    Operation: c <- a [op] b

    :param test: whether the instruction to be executed is TEST
    """
    b = self.mem.get(self.eip, off)
    self.eip += off
    b = to_int(b)

    a = to_int(self.reg.get(0, off))

    self.reg.eflags_set(Reg32.OF, 0)
    self.reg.eflags_set(Reg32.CF, 0)

    c = operation(a, b)

    self.reg.eflags_set(Reg32.SF, (c >> (off * 8 - 1)) & 1)

    c &= MAXVALS[off]

    self.reg.eflags_set(Reg32.ZF, c == 0)
    
    c = c.to_bytes(off, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], off))

    if not test:
        name = operation.__name__
        self.reg.set(0, c)
    else:
        name = 'test'

    debug('{} {}, imm{}({})'.format(name, [0, 'al', 'ax', 0, 'eax'][off], off * 8, b))


def bitwise_rm_imm(self, off, imm_sz, operation, test=False) -> bool:
    """
    [See `bitwise_al_imm` for description].
    """
    old_eip = self.eip

    RM, R = self.process_ModRM(off, off)

    if (operation == operator.and_):
        if (not test) and (R[1] != 4):
            self.eip = old_eip
            return False  # this is not AND
        elif test and (R[1] != 0):
            self.eip = old_eip
            return False  # this is not TEST
    elif (operation == operator.or_) and (R[1] != 1):
        self.eip = old_eip
        return False  # this is not OR
    elif (operation == operator.xor) and (R[1] != 6):
        self.eip = old_eip
        return False  # this is not XOR

    b = self.mem.get(self.eip, imm_sz)
    self.eip += imm_sz
    b = sign_extend(b, off)
    b = to_int(b)

    type, loc, _ = RM

    self.reg.eflags_set(Reg32.OF, 0)
    self.reg.eflags_set(Reg32.CF, 0)

    a = to_int((self.mem if type else self.reg).get(loc, off))
    c = operation(a, b)

    self.reg.eflags_set(Reg32.SF, (c >> (off * 8 - 1)) & 1)

    c &= MAXVALS[off]

    self.reg.eflags_set(Reg32.ZF, c == 0)
    
    c = c.to_bytes(off, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], off))

    if not test:
        name = operation.__name__
        (self.mem if type else self.reg).set(loc, c)
    else:
        name = 'test'

    debug('{0} {5}{1}({2}),imm{3}({4})'.format(name, off * 8, loc, imm_sz * 8, b, ('m' if type else 'r')))

    return True


def bitwise_rm_r(self, off, operation, test=False) -> None:
    """
    [See `bitwise_al_imm` for description].
    """
    RM, R = self.process_ModRM(off, off)

    type, loc, _ = RM

    self.reg.eflags_set(Reg32.OF, 0)
    self.reg.eflags_set(Reg32.CF, 0)

    a = to_int((self.mem if type else self.reg).get(loc, off))
    b = to_int(self.reg.get(R[1], off))

    c = operation(a, b)

    self.reg.eflags_set(Reg32.SF, (c >> (off * 8 - 1)) & 1)

    c &= MAXVALS[off]

    self.reg.eflags_set(Reg32.ZF, c == 0)
    
    c = c.to_bytes(off, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], off))

    if not test:
        name = operation.__name__
        (self.mem if type else self.reg).set(loc, c)
    else:
        name = 'test'

    debug('{0} {4}{1}({2}),r{1}({3})'.format(name, off * 8, loc, R[1], ('m' if type else '_r')))


def bitwise_r_rm(self, off, operation, test=False) -> None:
    """
    [See `bitwise_al_imm` for description].
    """
    RM, R = self.process_ModRM(off, off)

    type, loc, _ = RM

    self.reg.eflags_set(Reg32.OF, 0)
    self.reg.eflags_set(Reg32.CF, 0)

    a = to_int((self.mem if type else self.reg).get(loc, off))
    b = to_int(self.reg.get(R[1], off))

    c = operation(a, b)

    self.reg.eflags_set(Reg32.SF, (c >> (off * 8 - 1)) & 1)

    c &= MAXVALS[off]

    self.reg.eflags_set(Reg32.ZF, c == 0)
    
    c = c.to_bytes(off, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], off))

    if not test:
        name = operation.__name__
        self.reg.set(R[1], c)
    else:
        name = 'test'

    debug('{0} r{1}({2}),{4}{1}({3})'.format(name, off * 8, R[1], loc, ('m' if type else '_r')))


####################
# NEG / NOT
####################
def operation_not(a, off):
    return MAXVALS[off] - a


def operation_neg(a, off):
    return operation_not(a, off) + 1


def negnot_rm(self, off, operation) -> bool:
    """
    NEG: two's complement negate
    Flags:
        CF flag set to 0 if the source operand is 0; otherwise it is set to 1.
        OF (!), SF, ZF, AF(!), and PF flags are set according to the result.

    NOT: one's complement negation  (reverses bits)
    Flags:
        None affected
    """
    old_eip = self.eip

    RM, R = self.process_ModRM(off, off)

    if operation == 0:  # NEG
        if R[1] != 3:
            self.eip = old_eip
            return False  # this is not NEG
        operation = operation_neg
    elif operation == 1:  # NOT
        if R[1] != 2:
            self.eip = old_eip
            return False  # this is not NOT
        operation = operation_not
    else:
        raise ValueError("Invalid argument to __negnot_rm: this is an error in the VM")

    type, loc, _ = RM

    a = to_int((self.mem if type else self.reg).get(loc, off))
    if operation == operation_neg:
        self.reg.eflags_set(Reg32.CF, a != 0)

    b = operation(a, off) & MAXVALS[off]

    sign_b = (b >> (off * 8 - 1)) & 1

    if operation == operation_neg:
        self.reg.eflags_set(Reg32.SF, sign_b)
        self.reg.eflags_set(Reg32.ZF, b == 0)

    b = b.to_bytes(off, byteorder)

    if operation == operation_neg:
        self.reg.eflags_set(Reg32.PF, parity(b[0], off))

    self.reg.set(loc, b)

    debug('{0} {3}{1}({2})'.format(operation.__name__, off * 8, loc, ('m' if type else '_r')))

    return True
    
    

####################
# INC / DEC
####################
def incdec_rm(self, off, dec=False) -> bool:
    """
    Increment or decrement r/m8/16/32 by 1

    Flags:
        CF not affected
        OF, SF, ZF, AF, PF set according to the result

    Operation: c <- a +/- 1

    :param dec: whether the instruction to be executed is DEC. If False, INC is executed.
    """
    old_eip = self.eip

    RM, R = self.process_ModRM(off, off)

    if (not dec) and (R[1] != 0):
        self.eip = old_eip
        return False  # this is not INC
    elif dec and (R[1] != 1):
        self.eip = old_eip
        return False  # this is not DEC

    type, loc, _ = RM
    
    a = to_int((self.mem if type else self.reg).get(loc, off))
    b = 1
    
    c = a + (b if not dec else MAXVALS[off] - 1 + b)
    
    sign_a = (a >> (off * 8 - 1)) & 1
    sign_b = (b >> (off * 8 - 1)) & 1
    sign_c = (c >> (off * 8 - 1)) & 1
    
    if not dec:
        self.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
    else:
        self.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))
        
    self.reg.eflags_set(Reg32.SF, sign_c)

    c &= MAXVALS[off]

    self.reg.eflags_set(Reg32.ZF, c == 0)
    
    c = c.to_bytes(off, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], off))
    
    (self.mem if type else self.reg).set(loc, c)
    debug('{3} {0}{1}({2})'.format('m' if type else '_r', off * 8, loc, 'dec' if dec else 'inc'))
    
    return True
    
    
def incdec_r(self, off, op, dec=False) -> None:
    """
    [See `incdec_rm` for description].
    """
    loc = op & 0b111
    
    a = to_int(self.reg.get(loc, off))
    b = 1
    
    c = a + (b if not dec else MAXVALS[off] - 1 + b)
    
    sign_a = (a >> (off * 8 - 1)) & 1
    sign_b = (b >> (off * 8 - 1)) & 1
    sign_c = (c >> (off * 8 - 1)) & 1
    
    if not dec:
        self.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
    else:
        self.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))
        
    self.reg.eflags_set(Reg32.SF, sign_c)

    c &= MAXVALS[off]

    self.reg.eflags_set(Reg32.ZF, c == 0)
    
    c = c.to_bytes(off, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], off))
    
    self.reg.set(loc, c)
    debug('{3} {0}{1}({2})'.format('r', off * 8, loc, 'dec' if dec else 'inc'))



####################
# LEAVE
####################
def leave(self) -> None:
    """
    High-level procedure exit.

    Operation:
        1) ESP <- EBP
        2) EBP = stack_pop()
    """
    ESP, EBP = 4, 5  # depends on 'self.address_size' and 'self.operand_size'

    self.reg.set(ESP, self.reg.get(EBP, self.address_size))
    self.reg.set(EBP, self.stack_pop(self.operand_size))
