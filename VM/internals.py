from .debug import debug
from .CPU import to_int, byteorder

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
    data = self.mem.get(self.eip, off)
    self.eip += off

    r = op & 0b111
    self.reg.set(r, data)
    debug('mov r{0}({1}),imm{0}({2})'.format(off * 8, r, data))


def _VM__mov_rm_imm(self, off):
    RM, R = self.process_ModRM(off, off)
    if R[1] != 0:
        return False
    type, loc, _ = RM

    data = self.mem.get(self.eip, off)
    self.eip += off

    if not type:
        self.reg.set(loc, data)
        debug('mov _r{0}({1}),imm{0}({2})'.format(off * 8, loc, data))
    else:
        self.mem.set(loc, data)
        debug('mov m{0}({1}),imm{0}({2})'.format(off * 8, loc, data))
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
# ADD instruction
####################
def _VM__add_al_imm(self, off):
    imm = self.mem.get(self.eip, off)
    self.eip += off
    imm = to_int(imm)  # how to deal with signedness?

    tmp = to_int(self.reg.get(0, off)) + imm

    self.reg.set(0, tmp.to_bytes(off, byteorder))
    debug('add {}, imm{}({})'.format([0, 'al', 'ax', 0, 'eax'][off], off * 8, imm))


def _VM__add_rm_imm(self, off):
    imm = self.mem.get(self.eip, off)
    self.eip += off
    imm = to_int(imm)  # how to deal with signedness?

    RM, R = self.process_ModRM(off, off)

    if R[1] != 0:
        return False

    type, loc, _ = RM

    if not type:
        tmp = to_int(self.reg.get(loc, off)) + imm
        self.reg.set(loc, tmp.to_bytes(off, byteorder))
        debug('add r{0}({1}),imm{0}({2})'.format(off * 8, loc, imm))
    else:
        tmp = to_int(self.mem.get(loc, off)) + imm
        self.mem.set(loc, tmp.to_bytes(off, byteorder))
        debug('add m{0}({1}),imm{0}({2})'.format(off * 8, loc, imm))

    return True


def _VM__add_rm_r(self, off):
    RM, R = self.process_ModRM(off, off)

    type, loc, _ = RM

    if not type:
        tmp = to_int(self.reg.get(loc, off)) + to_int(self.reg.get(R[1], off))
        self.reg.set(loc, tmp.to_bytes(off, byteorder))
        debug('add _r{0}({1}),r{0}({2})'.format(off * 8, loc, R[1]))
    else:
        tmp = to_int(self.mem.get(loc, off)) + to_int(self.reg.get(R[1], off))
        self.mem.set(loc, tmp.to_bytes(off, byteorder))
        debug('add m{0}({1}),r{0}({2})'.format(off * 8, loc, R[1]))


def _VM__add_r_rm(self, off):
    RM, R = self.process_ModRM(off, off)

    type, loc, _ = RM

    if not type:
        tmp = to_int(self.reg.get(loc, off)) + to_int(self.reg.get(R[1], off))
        self.reg.set(R[1], tmp.to_bytes(off, byteorder))
        debug('add r{0}({1}),_r{0}({2})'.format(off * 8, R[1], loc))
    else:
        tmp = to_int(self.mem.get(loc, off)) + to_int(self.reg.get(R[1], off))
        self.reg.set(R[1], tmp.to_bytes(off, byteorder))
        debug('add r{0}({1}),m{0}({2})'.format(off * 8, R[1], loc))