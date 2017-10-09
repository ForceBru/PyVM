import operator
from .debug import debug
from .misc import sign_extend, parity, Shift
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
def mov_r_imm(self, op, _8bit) -> True:
    """
    Move data from one location (a) to another (b).

    Flags:
        None affected

    Operation: b <- a
    """
    sz = 1 if _8bit else self.operand_size

    imm = self.mem.get(self.eip, sz)
    self.eip += sz

    r = op & 0b111
    self.reg.set(r, imm)
    debug('mov r{0}({1}),imm{0}({2})'.format(sz * 8, r, imm))

    return True


def mov_rm_imm(self, _8bit) -> bool:
    """
    [See `mov_r_imm` for description].
    """
    sz = 1 if _8bit else self.operand_size
    old_eip = self.eip

    RM, R = self.process_ModRM(sz, sz)

    if R[1] != 0:
        self.eip = old_eip
        return False # this is not MOV

    type, loc, _ = RM

    imm = self.mem.get(self.eip, sz)
    self.eip += sz

    (self.mem if type else self.reg).set(loc, imm)
    debug('mov {0}{1}({2}),imm{1}({3})'.format(('m' if type else '_r'), sz * 8, loc, imm))

    return True


def mov_rm_r(self, _8bit) -> True:
    """
    [See `mov_r_imm` for description].
    """
    sz = 1 if _8bit else self.operand_size

    RM, R = self.process_ModRM(sz, sz)

    type, loc, _ = RM

    data = self.reg.get(R[1], R[2])

    (self.mem if type else self.reg).set(loc, data)
    debug('mov {0}{1}({2}),r{1}({3})'.format(('m' if type else '_r'), sz * 8, loc, data))

    return True


def mov_r_rm(self, _8bit) -> True:
    """
    [See `mov_r_imm` for description].
    """
    sz = 1 if _8bit else self.operand_size

    RM, R = self.process_ModRM(sz, sz)

    type, loc, _ = RM

    data = (self.mem if type else self.reg).get(loc, sz)
    self.reg.set(R[1], data)

    debug('mov r{1}({2}),{0}{1}({3})'.format(('m' if type else '_r'), sz * 8, R[1], data))

    return True


def mov_r_moffs(self, _8bit, reverse=False) -> True:
    """
    [See `mov_r_imm` for description].
    """
    sz = 1 if _8bit else self.operand_size

    loc = to_int(self.mem.get(self.eip, self.address_size))
    self.eip += self.address_size

    if reverse:
        data = self.reg.get(0, sz)
        self.mem.set(loc, data)
    else:
        data = self.mem.get(loc, sz)
        self.reg.set(0, data)

    msg = 'mov moffs{1}({2}), {0}({3})' if reverse else 'mov {0}, moffs{1}({2}:{3})'

    debug(msg.format({1: 'al', 2: 'ax', 4: 'eax'}[sz], sz * 8, loc, data))

    return True



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
def int_3(self) -> True:
    self.descriptors[2].write("[!] It's a trap! (literally)")

    return True


def int_imm(self) -> True:
    """
    Call to interrupt procedure.
    """
    imm = self.mem.get(self.eip, 1)  # always 8 bits
    imm = to_int(imm)
    self.eip += 1

    self.interrupt(imm)

    return True


####################
# PUSH
####################
def push_r(self, op) -> True:
    sz = self.operand_size

    loc = op & 0b111
    data = self.reg.get(loc, sz)
    debug('push r{}({})'.format(sz * 8, loc))
    self.stack_push(data)

    return True


def push_rm(self) -> bool:
    """
    Push data onto the stack.
    """
    old_eip = self.eip
    sz = self.operand_size

    RM, R = self.process_ModRM(sz, sz)

    if R[1] != 6:
        self.eip = old_eip
        return False  # this is not PUSH rm

    type, loc, _ = RM

    data = (self.mem if type else self.reg).get(loc, sz)
    self.stack_push(data)

    debug('push {2}{0}({1})'.format(sz * 8, data, ('m' if type else '_r')))
    return True


def push_imm(self, _8bit=False) -> True:
    """
    [See `push_rm` for description].
    """
    sz = 1 if _8bit else self.operand_size

    data = self.mem.get(self.eip, sz)
    self.eip += sz

    self.stack_push(data)

    debug('push imm{}({})'.format(sz * 8, data))

    return True


def push_sreg(self, reg: str) -> True:
    """
    Push a segment register onto the stack.

    :param reg: the name of the register to be pushed.
    """

    self.stack_push(getattr(self.reg, reg).to_bytes(2, byteorder))
    debug('push {}'.format(reg))

    return True


####################
# POP
####################
def pop_r(self, op) -> True:
    sz = self.operand_size

    loc = op & 0b111
    data = self.stack_pop(sz)
    self.reg.set(loc, data)
    debug('pop r{}({})'.format(sz * 8, loc))

    return True

def pop_rm(self) -> bool:
    """
    Pop data from the stack.
    """
    sz = self.operand_size
    old_eip = self.eip

    RM, R = self.process_ModRM(sz, sz)

    if R[1] != 0:
        self.eip = old_eip
        return False  # this is not POP rm

    type, loc, _ = RM

    data = self.stack_pop(sz)

    (self.mem if type else self.reg).set(loc, data)

    debug('pop {2}{0}({1})'.format(sz * 8, data, ('m' if type else '_r')))

    return True


def pop_sreg(self, reg: str, _32bit=False) -> True:
    sz = 4 if _32bit else 2

    data = self.stack_pop(sz)

    setattr(self.reg, reg, to_int(data, False))
    debug('pop {}'.format(reg))

    return True


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
def ret_near(self) -> True:
    """
    Return to calling procedure.
    """
    sz = self.operand_size
    self.eip = to_int(self.stack_pop(sz), True)

    debug("ret ({})".format(self.eip))

    return True


def ret_near_imm(self) -> True:
    """
    [See `ret_near` for description].
    """
    sz = 2  # always 16 bits
    self.eip = to_int(self.stack_pop(sz), True)

    imm = to_int(self.mem.get(self.eip, sz))
    self.eip += sz

    self.stack_pop(imm)

    debug("ret ({})".format(self.eip))

    return True


####################
# ADD / SUB / CMP / ADC / SBB
####################
def addsub_r_imm(self, _8bit, sub=False, cmp=False, carry=False) -> True:
    """
    Perform addition or subtraction.
    Flags:
        OF, SF, ZF, AF, CF, and PF flags are set according to the result.

    Operation: c <- a [op] b

    :param sub: indicates whether the instruction to be executed is SUB. If False, ADD is executed.
    :param cmp: indicates whether the instruction to be executed is CMP.
    :param carry: indicates whether the instruction to be executed is ADC or SBB. Must be combined with the `sub` parameter.
    """
    sz = 1 if _8bit else self.operand_size

    b = self.mem.get(self.eip, sz)
    self.eip += sz
    b = to_int(b)

    if carry:
        b += self.reg.eflags_get(Reg32.CF)

    a = to_int(self.reg.get(0, sz))

    c = a + (b if not sub else MAXVALS[sz] + 1 - b)
    
    sign_a = (a >> (sz * 8 - 1)) & 1
    sign_b = (b >> (sz * 8 - 1)) & 1
    sign_c = (c >> (sz * 8 - 1)) & 1
    
    if not sub:
        self.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.CF, c > MAXVALS[sz])
        self.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
    else:
        self.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.CF, b > a)
        self.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))
        
    self.reg.eflags_set(Reg32.SF, sign_c)

    c &= MAXVALS[sz]

    self.reg.eflags_set(Reg32.ZF, c == 0)

    c = c.to_bytes(sz, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], sz))
    
    if not cmp:
        self.reg.set(0, c)

    name = 'sub' if sub else 'add'
    debug('{} {}, imm{}({})'.format('cmp' if cmp else name, [0, 'al', 'ax', 0, 'eax'][sz], sz * 8, b))

    return True


def addsub_rm_imm(self, _8bit_op, _8bit_imm, sub=False, cmp=False, carry=False) -> bool:
    """
    [See `addsub_al_imm` for description].
    """
    sz = 1 if _8bit_op else self.operand_size
    imm_sz = 1 if _8bit_imm else self.operand_size

    assert sz >= imm_sz
    old_eip = self.eip

    RM, R = self.process_ModRM(sz, sz)

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
    b = sign_extend(b, sz)
    b = to_int(b)

    if carry:
        b += self.reg.eflags_get(Reg32.CF)
    
    type, loc, _ = RM

    a = to_int((self.mem if type else self.reg).get(loc, sz))
    c = a + (b if not sub else MAXVALS[sz] + 1 - b)
    
    sign_a = (a >> (sz * 8 - 1)) & 1
    sign_b = (b >> (sz * 8 - 1)) & 1
    sign_c = (c >> (sz * 8 - 1)) & 1
    
    if not sub:
        self.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.CF, c > MAXVALS[sz])
        self.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
    else:
        self.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.CF, b > a)
        self.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))
        
    self.reg.eflags_set(Reg32.SF, sign_c)

    c &= MAXVALS[sz]

    self.reg.eflags_set(Reg32.ZF, c == 0)
    
    c = c.to_bytes(sz, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], sz))

    if not cmp:
        (self.mem if type else self.reg).set(loc, c)

    name = 'sub' if sub else 'add'
    debug('{0} {5}{1}({2}),imm{3}({4})'.format('cmp' if cmp else name, sz * 8, loc, imm_sz * 8, b, ('m' if type else 'r')))

    return True


def addsub_rm_r(self, _8bit, sub=False, cmp=False, carry=False) -> True:
    """
    [See `addsub_al_imm` for description].
    """
    sz = 1 if _8bit else self.operand_size

    RM, R = self.process_ModRM(sz, sz)

    type, loc, _ = RM

    a = to_int((self.mem if type else self.reg).get(loc, sz))
    b = to_int(self.reg.get(R[1], sz))

    if carry:
        b += self.reg.eflags_get(Reg32.CF)

    c = a + (b if not sub else MAXVALS[sz] + 1 - b)

    sign_a = (a >> (sz * 8 - 1)) & 1
    sign_b = (b >> (sz * 8 - 1)) & 1
    sign_c = (c >> (sz * 8 - 1)) & 1
    
    if not sub:
        self.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.CF, c > MAXVALS[sz])
        self.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
    else:
        self.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.CF, b > a)
        self.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))
        
    self.reg.eflags_set(Reg32.SF, sign_c)

    c &= MAXVALS[sz]

    self.reg.eflags_set(Reg32.ZF, c == 0)
    
    c = c.to_bytes(sz, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], sz))

    if not cmp:
        (self.mem if type else self.reg).set(loc, c)

    name = 'sub' if sub else 'add'
    debug('{0} {4}{1}({2}),r{1}({3})'.format('cmp' if cmp else name, sz * 8, loc, R[1], ('m' if type else '_r')))

    return True


def addsub_r_rm(self, _8bit, sub=False, cmp=False, carry=False) -> True:
    """
    [See `addsub_al_imm` for description].
    """
    sz = 1 if _8bit else self.operand_size

    RM, R = self.process_ModRM(sz, sz)

    type, loc, _ = RM

    a = to_int((self.mem if type else self.reg).get(loc, sz))
    b = to_int(self.reg.get(R[1], sz))

    if carry:
        b += self.reg.eflags_get(Reg32.CF)

    c = a + (b if not sub else MAXVALS[sz] + 1 - b)

    sign_a = (a >> (sz * 8 - 1)) & 1
    sign_b = (b >> (sz * 8 - 1)) & 1
    sign_c = (c >> (sz * 8 - 1)) & 1
    
    if not sub:
        self.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.CF, c > MAXVALS[sz])
        self.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
    else:
        self.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.CF, b > a)
        self.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))
        
    self.reg.eflags_set(Reg32.SF, sign_c)

    c &= MAXVALS[sz]

    self.reg.eflags_set(Reg32.ZF, c == 0)
    
    c = c.to_bytes(sz, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], sz))

    if not cmp:
        self.reg.set(R[1], c)

    name = 'sub' if sub else 'add'
    debug('{0} r{1}({2}),{4}{1}({3})'.format('cmp' if cmp else name, sz * 8, R[1], loc, ('m' if type else '_r')))

    return True


####################
# AND / OR / XOR / TEST
####################
def bitwise_r_imm(self, _8bit, operation, test=False) -> True:
    """
    Perform a bitwise operation.
    Flags:
        OF, CF cleared
        SF, ZF, PF set according to the result
        AF undefined

    Operation: c <- a [op] b

    :param test: whether the instruction to be executed is TEST
    """
    sz = 1 if _8bit else self.operand_size
    b = self.mem.get(self.eip, sz)
    self.eip += sz
    b = to_int(b)

    a = to_int(self.reg.get(0, sz))

    self.reg.eflags_set(Reg32.OF, 0)
    self.reg.eflags_set(Reg32.CF, 0)

    c = operation(a, b)

    self.reg.eflags_set(Reg32.SF, (c >> (sz * 8 - 1)) & 1)

    c &= MAXVALS[sz]

    self.reg.eflags_set(Reg32.ZF, c == 0)
    
    c = c.to_bytes(sz, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], sz))

    if not test:
        name = operation.__name__
        self.reg.set(0, c)
    else:
        name = 'test'

    debug('{} {}, imm{}({})'.format(name, [0, 'al', 'ax', 0, 'eax'][sz], sz * 8, b))

    return True


def bitwise_rm_imm(self, _8bit, _8bit_imm, operation, test=False) -> bool:
    """
    [See `bitwise_al_imm` for description].
    """
    sz = 1 if _8bit else self.operand_size
    imm_sz = 1 if _8bit_imm else self.operand_size
    old_eip = self.eip

    RM, R = self.process_ModRM(sz, sz)

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
    b = sign_extend(b, sz)
    b = to_int(b)

    type, loc, _ = RM

    self.reg.eflags_set(Reg32.OF, 0)
    self.reg.eflags_set(Reg32.CF, 0)

    a = to_int((self.mem if type else self.reg).get(loc, sz))
    c = operation(a, b)

    self.reg.eflags_set(Reg32.SF, (c >> (sz * 8 - 1)) & 1)

    c &= MAXVALS[sz]

    self.reg.eflags_set(Reg32.ZF, c == 0)
    
    c = c.to_bytes(sz, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], sz))

    if not test:
        name = operation.__name__
        (self.mem if type else self.reg).set(loc, c)
    else:
        name = 'test'

    debug('{0} {5}{1}({2}),imm{3}({4})'.format(name, sz * 8, loc, imm_sz * 8, b, ('m' if type else 'r')))

    return True


def bitwise_rm_r(self, _8bit, operation, test=False) -> True:
    """
    [See `bitwise_al_imm` for description].
    """
    sz = 1 if _8bit else self.operand_size
    RM, R = self.process_ModRM(sz, sz)

    type, loc, _ = RM

    self.reg.eflags_set(Reg32.OF, 0)
    self.reg.eflags_set(Reg32.CF, 0)

    a = to_int((self.mem if type else self.reg).get(loc, sz))
    b = to_int(self.reg.get(R[1], sz))

    c = operation(a, b)

    self.reg.eflags_set(Reg32.SF, (c >> (sz * 8 - 1)) & 1)

    c &= MAXVALS[sz]

    self.reg.eflags_set(Reg32.ZF, c == 0)
    
    c = c.to_bytes(sz, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], sz))

    if not test:
        name = operation.__name__
        (self.mem if type else self.reg).set(loc, c)
    else:
        name = 'test'

    debug('{0} {4}{1}({2}),r{1}({3})'.format(name, sz * 8, loc, R[1], ('m' if type else '_r')))

    return True


def bitwise_r_rm(self, _8bit, operation, test=False) -> True:
    """
    [See `bitwise_al_imm` for description].
    """
    sz = 1 if _8bit else self.operand_size
    RM, R = self.process_ModRM(sz, sz)

    type, loc, _ = RM

    self.reg.eflags_set(Reg32.OF, 0)
    self.reg.eflags_set(Reg32.CF, 0)

    a = to_int((self.mem if type else self.reg).get(loc, sz))
    b = to_int(self.reg.get(R[1], sz))

    c = operation(a, b)

    self.reg.eflags_set(Reg32.SF, (c >> (sz * 8 - 1)) & 1)

    c &= MAXVALS[sz]

    self.reg.eflags_set(Reg32.ZF, c == 0)
    
    c = c.to_bytes(sz, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], sz))

    if not test:
        name = operation.__name__
        self.reg.set(R[1], c)
    else:
        name = 'test'

    debug('{0} r{1}({2}),{4}{1}({3})'.format(name, sz * 8, R[1], loc, ('m' if type else '_r')))

    return True


####################
# NEG / NOT
####################
def operation_not(a, off):
    return MAXVALS[off] - a


def operation_neg(a, off):
    return operation_not(a, off) + 1


def negnot_rm(self, _8bit, operation) -> bool:
    """
    NEG: two's complement negate
    Flags:
        CF flag set to 0 if the source operand is 0; otherwise it is set to 1.
        OF (!), SF, ZF, AF(!), and PF flags are set according to the result.

    NOT: one's complement negation  (reverses bits)
    Flags:
        None affected
    """
    sz = 1 if _8bit else self.operand_size
    old_eip = self.eip

    RM, R = self.process_ModRM(sz, sz)

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

    a = to_int((self.mem if type else self.reg).get(loc, sz))
    if operation == operation_neg:
        self.reg.eflags_set(Reg32.CF, a != 0)

    b = operation(a, sz) & MAXVALS[sz]

    sign_b = (b >> (sz * 8 - 1)) & 1

    if operation == operation_neg:
        self.reg.eflags_set(Reg32.SF, sign_b)
        self.reg.eflags_set(Reg32.ZF, b == 0)

    b = b.to_bytes(sz, byteorder)

    if operation == operation_neg:
        self.reg.eflags_set(Reg32.PF, parity(b[0], sz))

    self.reg.set(loc, b)

    debug('{0} {3}{1}({2})'.format(operation.__name__, sz * 8, loc, ('m' if type else '_r')))

    return True
    
    

####################
# INC / DEC
####################
def incdec_rm(self, _8bit, dec=False) -> bool:
    """
    Increment or decrement r/m8/16/32 by 1

    Flags:
        CF not affected
        OF, SF, ZF, AF, PF set according to the result

    Operation: c <- a +/- 1

    :param dec: whether the instruction to be executed is DEC. If False, INC is executed.
    """
    sz = 1 if _8bit else self.operand_size
    old_eip = self.eip

    RM, R = self.process_ModRM(sz, sz)

    if (not dec) and (R[1] != 0):
        self.eip = old_eip
        return False  # this is not INC
    elif dec and (R[1] != 1):
        self.eip = old_eip
        return False  # this is not DEC

    type, loc, _ = RM
    
    a = to_int((self.mem if type else self.reg).get(loc, sz))
    b = 1
    
    c = a + (b if not dec else MAXVALS[sz] - 1 + b)
    
    sign_a = (a >> (sz * 8 - 1)) & 1
    sign_b = (b >> (sz * 8 - 1)) & 1
    sign_c = (c >> (sz * 8 - 1)) & 1
    
    if not dec:
        self.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
    else:
        self.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))
        
    self.reg.eflags_set(Reg32.SF, sign_c)

    c &= MAXVALS[sz]

    self.reg.eflags_set(Reg32.ZF, c == 0)
    
    c = c.to_bytes(sz, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], sz))
    
    (self.mem if type else self.reg).set(loc, c)
    debug('{3} {0}{1}({2})'.format('m' if type else '_r', sz * 8, loc, 'dec' if dec else 'inc'))
    
    return True
    
    
def incdec_r(self, op, _8bit, dec=False) -> True:
    """
    [See `incdec_rm` for description].
    """
    sz = 1 if _8bit else self.operand_size
    loc = op & 0b111
    
    a = to_int(self.reg.get(loc, sz))
    b = 1
    
    c = a + (b if not dec else MAXVALS[sz] - 1 + b)
    
    sign_a = (a >> (sz * 8 - 1)) & 1
    sign_b = (b >> (sz * 8 - 1)) & 1
    sign_c = (c >> (sz * 8 - 1)) & 1
    
    if not dec:
        self.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
    else:
        self.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
        self.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))
        
    self.reg.eflags_set(Reg32.SF, sign_c)

    c &= MAXVALS[sz]

    self.reg.eflags_set(Reg32.ZF, c == 0)
    
    c = c.to_bytes(sz, byteorder)
    
    self.reg.eflags_set(Reg32.PF, parity(c[0], sz))
    
    self.reg.set(loc, c)
    debug('{3} {0}{1}({2})'.format('r', sz * 8, loc, 'dec' if dec else 'inc'))

    return True



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


####################
# LEA
####################
def lea(self) -> True:
    RM, R = self.process_ModRM(self.operand_size, self.operand_size)

    type, loc, sz = RM

    if (self.operand_size == 2) and (self.address_size == 2):
        tmp = loc
    elif (self.operand_size == 2) and (self.address_size == 4):
        tmp = loc & 0xffff
    elif (self.operand_size == 4) and (self.address_size == 2):
        tmp = loc
    elif (self.operand_size == 4) and (self.address_size == 4):
        tmp = loc
    else:
        raise RuntimeError("Invalid operand size / address size")

    self.reg.set(R[1], tmp.to_bytes(self.operand_size, byteorder))

    return True
    

####################
# SAL / SAR / SHL / SHR
####################
def shift(self, operation, cnt, _8bit) -> True:
	sz = 1 if _8bit else self.operand_size
	old_eip = self.eip
	
	RM, R = self.process_ModRM(self.operand_size, self.operand_size)
	
	if (operation == Shift.SHL) and (R[1] != 4):
		self.eip = old_eip
		return False
	elif (operation == Shift.SHR) and (R[1] != 5):
		self.eip = old_eip
		return False
	elif (operation == Shift.SAR) and (R[1] != 7):
		self.eip = old_eip
		return False
		
	_cnt = cnt
	
	if cnt == Shift.C_ONE:
		cnt = 1
	elif cnt == Shift.C_CL:
		cnt = to_int(self.reg.get(1, 1))
	elif cnt == Shift.C_imm8:
		cnt = to_int(self.mem.get(self.eip, 1))
		self.eip += 1
	else:
		raise RuntimeError('Invalid count')
		
	tmp_cnt = cnt & 0x1F
	type, loc, _ = RM
	
	dst = to_int((self.mem if type else self.reg).get(loc, sz), signed=(operation==Shift.SAR))
	tmp_dst = dst
	
	if cnt == 0:
		return True
	
	while tmp_cnt:
		if operation == Shift.SHL:
			self.reg.eflags_set(Reg32.CF, (dst >> (sz * 8)) & 1)
			dst <<= 1
		else:
			self.reg.eflags_set(Reg32.CF, dst & 1)
			dst >>= 1
			
		tmp_cnt -= 1
		
	if cnt & 0x1F == 1:
		if operation == Shift.SHL:
			self.reg.eflags_set(Reg32.OF, ((dst >> (sz * 8)) & 1) ^ self.reg.eflags_get(Reg32.CF))
		elif operation == Shift.SAR:
			self.reg.eflags_set(Reg32.OF, 0)
		else:
			self.reg.eflags_set(Reg32.OF, (tmp_dst >> (sz * 8)) & 1)
	
	sign_dst = (dst >> (sz * 8 - 1)) & 1
	self.reg.eflags_set(Reg32.SF, sign_dst)
	
	dst &= MAXVALS[sz]

	self.reg.eflags_set(Reg32.ZF, dst == 0)

	dst = dst.to_bytes(sz, byteorder)

	self.reg.eflags_set(Reg32.PF, parity(dst[0], sz))
	
	(self.mem if type else self.reg).set(loc, dst)
	
	if operation == Shift.SHL:
		name = 'shl'
	elif operation == Shift.SHR:
		name = 'shr'
	elif operation == Shift.SAR:
		name = 'sar'
		
	if _cnt == Shift.C_ONE:
		op = ''
	elif _cnt == Shift.C_CL:
		op = ',cl'
	elif _cnt == Shift.C_imm8:
		op = ',imm8'
		
	debug('{} {}{}{}'.format(name, 'm' if type else '_r', sz * 8, op))
	
	return True
