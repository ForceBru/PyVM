from .debug import debug
from .CPU import to_int, byteorder
from .Registers import Reg32

'''
These are the implementations of various instructions grouped in a submodule to avoid code duplication.
These functions are only to be called from `__init__.py`.

Each function should be named based on the following scheme:
    _VM__<mnemonic>_<arg1>_<arg2>

Each block of functions (i.e., functions implementing the same instruction) should be preceded by a comment in the form:
    ####################
    # <INSTRUCTION MNEMONIC> instruction
    ####################
'''

####################
# MOV instruction
####################
def _VM__mov_r_imm(self, off, op):
    imm = self.mem.get(self.eip, off)
    self.eip += off

    r = op & 0b111
    self.reg.set(r, imm)
    debug('mov r{0}({1}),imm{0}({2})'.format(off * 8, r, imm))


def _VM__mov_rm_imm(self, off):
    RM, R = self.process_ModRM(off, off)
    if R[1] != 0:
        return False
    type, loc, _ = RM

    imm = self.mem.get(self.eip, off)
    self.eip += off

    if not type:
        self.reg.set(loc, imm)
        debug('mov _r{0}({1}),imm{0}({2})'.format(off * 8, loc, imm))
    else:
        self.mem.set(loc, imm)
        debug('mov m{0}({1}),imm{0}({2})'.format(off * 8, loc, imm))
    return True


def _VM__mov_rm_r(self, off):
    RM, R = self.process_ModRM(off, off)

    type, loc, _ = RM

    data = self.reg.get(R[1], R[2])
    if not type:
        self.reg.set(loc, data)
        debug('mov _r{0}({1}),r{0}({2})'.format(off * 8, loc, data))
    else:
        self.mem.set(loc, data)
        debug('mov m{0}({1}),r{0}({2})'.format(off * 8, loc, data))


def _VM__mov_r_rm(self, off):
    RM, R = self.process_ModRM(off, off)

    type, loc, sz = RM

    if not type:
        data = self.reg.get(loc, sz)
        self.reg.set(R[1], data)
        debug('mov r{0}({1}),_r{0}({2})'.format(off * 8, R[1], data))
    else:
        data = self.mem.get(loc, sz)
        self.reg.set(R[1], data)
        debug('mov r{0}({1}),m{0}({2})'.format(off * 8, R[1], data))


def _VM__mov_eax_moffs(self, off):
    loc = to_int(self.mem.get(self.eip, self.address_size))
    self.eip += self.address_size

    data = self.mem.get(loc, off)
    self.reg.set(0, data)
    debug('mov {}, moffs{}({}:{})'.format({1: 'al', 2: 'ax', 4: 'eax'}[off], off * 8, loc, data))


def _VM__mov_moffs_eax(self, off):
    loc = to_int(self.mem.get(self.eip, self.address_size))
    self.eip += self.address_size

    data = self.reg.get(0, off)
    self.mem.set(loc, data)
    debug('mov moffs{}({}), {}({})'.format(off * 8, loc, {1: 'al', 2: 'ax', 4: 'eax'}[off], data))



####################
# JMP instruction
####################	
def _VM__jmp_rel(self, off):
    d = self.mem.get(self.eip, off)
    d = to_int(d, True)
    self.eip += off

    self.eip += d
    debug('jmp rel{}({})'.format(off * 8, self.eip))


####################
# ADD/SUB instructions
####################
MAXVALS = [None, (1 << 8) - 1, (1 << 16) - 1, None, (1 << 32) - 1]
SIGNS   = [None, 1 << 8 - 1, 1 << 16 - 1, None, 1 << 32 - 1]


def _VM__addsub_al_imm(self, off, sub=False, cmp=False):
    imm = self.mem.get(self.eip, off)
    self.eip += off
    imm = to_int(imm)

    a = to_int(self.reg.get(0, off))

    tmp = a + (imm if not sub else MAXVALS[off] + 1 - imm)

    self.reg.eflags_set(Reg32.SF, (tmp >> (off * 8 - 1)) & 1)
    self.reg.eflags_set(Reg32.OF, tmp > MAXVALS[off])

    tmp &= MAXVALS[off]

    self.reg.eflags_set(Reg32.ZF, tmp == 0)

    if not cmp:
        self.reg.set(0, tmp.to_bytes(off, byteorder))

    name = 'sub' if sub else 'add'
    debug('{} {}, imm{}({})'.format('cmp' if cmp else name, [0, 'al', 'ax', 0, 'eax'][off], off * 8, imm))


def _VM__addsub_rm_imm(self, off, imm_sz, sub=False, cmp=False):
    old_eip = self.eip

    RM, R = self.process_ModRM(off, off)

    imm = self.mem.get(self.eip, imm_sz)
    self.eip += imm_sz
    imm = to_int(imm)

    if (not sub) and (R[1] != 0):
        self.eip = old_eip
        return False  # this is not ADD
    elif sub:
        if not cmp and (R[1] != 5):
            self.eip = old_eip
            return False  # this is not SUB
        elif cmp and (R[1] != 7):
            self.eip = old_eip
            return False  # this is not CMP

    type, loc, _ = RM

    if not type:
        a = to_int(self.reg.get(loc, off))

        tmp = a + (imm if not sub else MAXVALS[off] + 1 - imm)

        self.reg.eflags_set(Reg32.SF, (tmp >> (off * 8 - 1)) & 1)
        self.reg.eflags_set(Reg32.OF, tmp > MAXVALS[off])

        tmp &= MAXVALS[off]

        self.reg.eflags_set(Reg32.ZF, tmp == 0)

        if not cmp:
            self.reg.set(loc, tmp.to_bytes(off, byteorder))

        name = 'sub' if sub else 'add'
        debug('{} r{}({}),imm{}({})'.format('cmp' if cmp else name, off * 8, loc, imm_sz * 8, imm))
    else:
        a = to_int(self.mem.get(loc, off))

        tmp = a + (imm if not sub else MAXVALS[off] + 1 - imm)

        self.reg.eflags_set(Reg32.SF, (tmp >> (off * 8 - 1)) & 1)
        self.reg.eflags_set(Reg32.OF, tmp > MAXVALS[off])

        tmp &= MAXVALS[off]

        self.reg.eflags_set(Reg32.ZF, tmp == 0)

        if not cmp:
            self.mem.set(loc, tmp.to_bytes(off, byteorder))

        name = 'sub' if sub else 'add'
        debug('{} m{}({}),imm{}({})'.format('cmp' if cmp else name, off * 8, loc, imm_sz * 8, imm))

    return True


def _VM__addsub_rm_r(self, off, sub=False, cmp=False):
    RM, R = self.process_ModRM(off, off)

    type, loc, _ = RM

    if not type:
        a = to_int(self.reg.get(loc, off))
        b = to_int(self.reg.get(R[1], off))

        tmp = a + (b if not sub else MAXVALS[off] + 1 - b)

        self.reg.eflags_set(Reg32.SF, (tmp >> (off * 8 - 1)) & 1)
        self.reg.eflags_set(Reg32.OF, tmp > MAXVALS[off])

        tmp &= MAXVALS[off]

        self.reg.eflags_set(Reg32.ZF, tmp == 0)

        if not cmp:
            self.reg.set(loc, tmp.to_bytes(off, byteorder))

        name = 'sub' if sub else 'add'
        debug('{0} _r{1}({2}),r{1}({3})'.format('cmp' if cmp else name, off * 8, loc, R[1]))
    else:
        a = to_int(self.mem.get(loc, off))
        b = to_int(self.reg.get(R[1], off))

        tmp = a + (b if not sub else MAXVALS[off] + 1 - b)

        self.reg.eflags_set(Reg32.SF, (tmp >> (off * 8 - 1)) & 1)
        self.reg.eflags_set(Reg32.OF, tmp > MAXVALS[off])

        tmp &= MAXVALS[off]

        self.reg.eflags_set(Reg32.ZF, tmp == 0)

        if not cmp:
            self.mem.set(loc, tmp.to_bytes(off, byteorder))

        name = 'sub' if sub else 'add'
        debug('{0} m{1}({2}),r{1}({3})'.format('cmp' if cmp else name, off * 8, loc, R[1]))


def _VM__addsub_r_rm(self, off, sub=False, cmp=False):
    RM, R = self.process_ModRM(off, off)

    type, loc, _ = RM

    if not type:
        a = to_int(self.reg.get(loc, off))
        b = to_int(self.reg.get(R[1], off))

        tmp = a + (b if not sub else MAXVALS[off] + 1 - b)

        self.reg.eflags_set(Reg32.SF, (tmp >> (off * 8 - 1)) & 1)
        self.reg.eflags_set(Reg32.OF, tmp > MAXVALS[off])

        tmp &= MAXVALS[off]

        self.reg.eflags_set(Reg32.ZF, tmp == 0)

        if not cmp:
            self.reg.set(R[1], tmp.to_bytes(off, byteorder))

        name = 'sub' if sub else 'add'
        debug('{0} r{1}({2}),_r{1}({3})'.format('cmp' if cmp else name, off * 8, R[1], loc))
    else:
        a = to_int(self.mem.get(loc, off))
        b = to_int(self.reg.get(R[1], off))
        if not sub:
            tmp = a + b
        else:
            tmp = a + MAXVALS[off] + 1 - b

            self.reg.eflags_set(Reg32.SF, (tmp >> (off * 8 - 1)) & 1)
        self.reg.eflags_set(Reg32.OF, tmp > MAXVALS[off])

        tmp &= MAXVALS[off]

        self.reg.eflags_set(Reg32.ZF, tmp == 0)

        if not cmp:
            self.reg.set(R[1], tmp.to_bytes(off, byteorder))

        name = 'sub' if sub else 'add'
        debug('{0} r{1}({2}),m{1}({3})'.format('cmp' if cmp else name, off * 8, R[1], loc))
