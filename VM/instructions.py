import operator
from .debug import debug
from .misc import sign_extend, parity, Shift
from .CPU import to_int, byteorder
from .Registers import Reg32

from unittest.mock import MagicMock

'''
These are the implementations of various instructions grouped in a submodule to avoid code duplication.

Each class or function implements a single instruction or many similar instructions.
These implementations are only to be used in `__init__.py`.

Each class should have the same name as the mnemonic it implements, in all caps. The functions inside any class
should be decorated with `@staticmethod` and should have names that indicate the type of arguments of the instruction implemented.

For example:
    mov eax, 0x1234   -> r_imm  (mov register, immediate)
    mov [eax], 0x1234 -> rm_imm (mov memory, immediate)
    
    int 0x80          -> imm (int immediate)
    
Functions that implement standalone instructions (i.e. they are not a part of a class) may have arbitrary names.

Each class or function may be preceded by a comment in the form:
    ####################
    # <INSTRUCTION MNEMONIC>[ / <another INSTRUCTION MNEMONIC>]*
    ####################
'''
MAXVALS = [None, (1 << 8) - 1, (1 << 16) - 1, None, (1 << 32) - 1]  # MAXVALS[n] is the maximum value of an unsigned n-bit number
SIGNS   = [None, 1 << 8 - 1, 1 << 16 - 1, None, 1 << 32 - 1]  # SIGNS[n] is the maximum absolute value of a signed n-bit number

####################
# MOV
####################
class MOV:
    """
    Move data from one location (a) to another (b).

    Flags:
        None affected

    Operation: b <- a
    """
    # TODO: implement MOV with sreg
    rm_sreg = MagicMock(side_effect=RuntimeError('MOV does not support segment registers yet'))

    @staticmethod
    def r_imm(vm, _8bit) -> True:
        sz = 1 if _8bit else vm.operand_size

        imm = vm.mem.get(vm.eip, sz)
        vm.eip += sz

        r = vm.opcode & 0b111
        vm.reg.set(r, imm)
        debug('mov r{0}({1}),imm{0}({2})'.format(sz * 8, r, imm))

        return True

    @staticmethod
    def rm_imm(vm, _8bit) -> bool:
        """
        [See `r_imm` for description].
        """
        sz = 1 if _8bit else vm.operand_size
        old_eip = vm.eip

        RM, R = vm.process_ModRM(sz, sz)

        if R[1] != 0:
            vm.eip = old_eip
            return False # this is not MOV

        type, loc, _ = RM

        imm = vm.mem.get(vm.eip, sz)
        vm.eip += sz

        (vm.mem if type else vm.reg).set(loc, imm)
        debug('mov {0}{1}({2}),imm{1}({3})'.format(('m' if type else '_r'), sz * 8, loc, imm))

        return True

    @staticmethod
    def rm_r(vm, _8bit, reverse=False) -> True:
        """
        [See `r_imm` for description].
        """
        sz = 1 if _8bit else vm.operand_size

        RM, R = vm.process_ModRM(sz, sz)

        type, loc, _ = RM

        if reverse:
            data = (vm.mem if type else vm.reg).get(loc, sz)
            vm.reg.set(R[1], data)

            debug('mov r{1}({2}),{0}{1}({3})'.format(('m' if type else '_r'), sz * 8, R[1], data))
        else:
            data = vm.reg.get(R[1], R[2])
            (vm.mem if type else vm.reg).set(loc, data)

            debug('mov {0}{1}({2}),r{1}({3})'.format(('m' if type else '_r'), sz * 8, loc, data))

        return True

    @staticmethod
    def r_moffs(vm, _8bit, reverse=False) -> True:
        sz = 1 if _8bit else vm.operand_size

        loc = to_int(vm.mem.get(vm.eip, vm.address_size))
        vm.eip += vm.address_size

        if reverse:
            data = vm.reg.get(0, sz)
            vm.mem.set(loc, data)
        else:
            data = vm.mem.get(loc, sz)
            vm.reg.set(0, data)

        msg = 'mov moffs{1}({2}), {0}({3})' if reverse else 'mov {0}, moffs{1}({2}:{3})'

        debug(msg.format({1: 'al', 2: 'ax', 4: 'eax'}[sz], sz * 8, loc, data))

        return True


####################
# JMP
####################
class JMP:
    """
        Jump to a memory address.

        Operation:
            EIP = memory_location
    """
    # TODO: implement jumps to pointers
    ptr = MagicMock(side_effect=RuntimeError('Jumps to pointers not implemented yet'))

    @staticmethod
    def rel(vm, _8bit, jump=compile('True', 'jump', 'eval')) -> True:
        sz = 1 if _8bit else vm.operand_size
    
        d = vm.mem.get(vm.eip, sz)
        d = to_int(d, True)
        vm.eip += sz
    
        if not eval(jump):
            return True

        vm.eip += d
    
        assert vm.eip in vm.mem.bounds
    
        debug('jmp rel{}({})'.format(sz * 8, hex(vm.eip)))
        return True

    @staticmethod
    def rm_m(vm) -> bool:
        old_eip = vm.eip

        sz = vm.operand_size
        RM, R = vm.process_ModRM(sz, sz)

        if R[1] == 4:  # this is jmp r/m
            disp = vm.mem.get(vm.eip, sz)
            vm.eip = to_int(disp) & MAXVALS[sz]

            assert vm.eip in vm.mem.bounds

            debug('jmp rm{}({})'.format(sz * 8, vm.eip))

            return True
        elif R[1] == 5:  # this is jmp m
            addr = to_int(vm.mem.get(vm.eip, vm.address_size))
            disp = vm.mem.get(addr, sz)
            vm.eip = to_int(disp) & MAXVALS[sz]

            assert vm.eip in vm.mem.bounds

            debug('jmp m{}({})'.format(sz * 8, vm.eip))

            return True

        vm.eip = old_eip
        return False


####################
# INT
####################
class INT:
    """
    Call to interrupt procedure.
    """
    @staticmethod
    def _3(vm) -> True:
        vm.descriptors[2].write("[!] It's a trap! (literally)")

        return True

    @staticmethod
    def imm(vm) -> True:
        imm = vm.mem.get(vm.eip, 1)  # always 8 bits
        imm = to_int(imm)
        vm.eip += 1

        vm.interrupt(imm)

        return True


####################
# PUSH
####################
class PUSH:
    @staticmethod
    def r(vm) -> True:
        sz = vm.operand_size

        loc = vm.opcode & 0b111
        data = vm.reg.get(loc, sz)
        debug('push r{}({})'.format(sz * 8, loc))
        vm.stack_push(data)

        return True

    @staticmethod
    def rm(vm) -> bool:
        """
        Push data onto the stack.
        """
        old_eip = vm.eip
        sz = vm.operand_size

        RM, R = vm.process_ModRM(sz, sz)

        if R[1] != 6:
            vm.eip = old_eip
            return False  # this is not PUSH rm

        type, loc, _ = RM

        data = (vm.mem if type else vm.reg).get(loc, sz)
        vm.stack_push(data)

        debug('push {2}{0}({1})'.format(sz * 8, data, ('m' if type else '_r')))
        return True

    @staticmethod
    def imm(vm, _8bit=False) -> True:
        sz = 1 if _8bit else vm.operand_size

        data = vm.mem.get(vm.eip, sz)
        vm.eip += sz

        vm.stack_push(data)

        debug('push imm{}({})'.format(sz * 8, data))

        return True

    @staticmethod
    def sreg(vm, reg: str) -> True:
        """
        Push a segment register onto the stack.

        :param reg: the name of the register to be pushed.
        """

        vm.stack_push(getattr(vm.reg, reg).to_bytes(2, byteorder))
        debug('push {}'.format(reg))

        return True


####################
# POP
####################
class POP:
    """
    Pop data from the stack.
    """

    @staticmethod
    def r(vm) -> True:
        sz = vm.operand_size

        loc = vm.opcode & 0b111
        data = vm.stack_pop(sz)
        vm.reg.set(loc, data)
        debug('pop r{}({})'.format(sz * 8, loc))

        return True

    @staticmethod
    def rm(vm) -> bool:
        sz = vm.operand_size
        old_eip = vm.eip

        RM, R = vm.process_ModRM(sz, sz)

        if R[1] != 0:
            vm.eip = old_eip
            return False  # this is not POP rm

        type, loc, _ = RM

        data = vm.stack_pop(sz)

        (vm.mem if type else vm.reg).set(loc, data)

        debug('pop {2}{0}({1})'.format(sz * 8, data, ('m' if type else '_r')))

        return True

    @staticmethod
    def sreg(vm, reg: str, _32bit=False) -> True:
        sz = 4 if _32bit else 2

        data = vm.stack_pop(sz)

        setattr(vm.reg, reg, to_int(data, False))
        debug('pop {}'.format(reg))

        return True


####################
# CALL
####################
class CALL:
    """
    Call a procedure.
    """

    # TODO: implement far calls
    rm_m = MagicMock(side_effect=RuntimeError('CALL r/m or m is not supported yet'))
    ptr = MagicMock(side_effect=RuntimeError('CALL ptr is not supported yet'))

    @staticmethod
    def rel(vm) -> True:
        sz = vm.operand_size
        dest = vm.mem.get(vm.eip, sz)
        vm.eip += sz
        dest = to_int(dest, True)
        tmpEIP = vm.eip + dest

        assert tmpEIP in vm.mem.bounds

        vm.stack_push(vm.eip.to_bytes(sz, byteorder, signed=True))
        vm.eip = tmpEIP

        debug("call rel{}({})".format(sz * 8, vm.eip))
        return True


####################
# RET
####################
class RET:
    """
    Return to calling procedure.
    """

    # TODO: implement far returns
    far = MagicMock(side_effect=RuntimeError('RET far is not supported yet'))
    far_imm = MagicMock(side_effect=RuntimeError('RET far imm is not supported yet'))

    @staticmethod
    def near(vm) -> True:
        sz = vm.operand_size
        vm.eip = to_int(vm.stack_pop(sz), True)

        debug("ret ({})".format(vm.eip))

        return True

    @staticmethod
    def near_imm(vm) -> True:
        sz = 2  # always 16 bits
        vm.eip = to_int(vm.stack_pop(sz), True)

        imm = to_int(vm.mem.get(vm.eip, sz))
        vm.eip += sz

        vm.stack_pop(imm)

        debug("ret ({})".format(vm.eip))

        return True


####################
# ADD / SUB / CMP / ADC / SBB
####################
class ADDSUB:
    """
    Perform addition or subtraction.
    Flags:
        OF, SF, ZF, AF, CF, and PF flags are set according to the result.

    Operation: c <- a [op] b

    :param sub: indicates whether the instruction to be executed is SUB. If False, ADD is executed.
    :param cmp: indicates whether the instruction to be executed is CMP.
    :param carry: indicates whether the instruction to be executed is ADC or SBB. Must be combined with the `sub` parameter.
    """
    @staticmethod
    def r_imm(vm, _8bit, sub=False, cmp=False, carry=False) -> True:
        sz = 1 if _8bit else vm.operand_size

        b = vm.mem.get(vm.eip, sz)
        vm.eip += sz
        b = to_int(b)

        if carry:
            b += vm.reg.eflags_get(Reg32.CF)

        a = to_int(vm.reg.get(0, sz))

        c = a + (b if not sub else MAXVALS[sz] + 1 - b)

        sign_a = (a >> (sz * 8 - 1)) & 1
        sign_b = (b >> (sz * 8 - 1)) & 1
        sign_c = (c >> (sz * 8 - 1)) & 1

        if not sub:
            vm.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.CF, c > MAXVALS[sz])
            vm.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
        else:
            vm.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.CF, b > a)
            vm.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))

        vm.reg.eflags_set(Reg32.SF, sign_c)

        c &= MAXVALS[sz]

        vm.reg.eflags_set(Reg32.ZF, c == 0)

        c = c.to_bytes(sz, byteorder)

        vm.reg.eflags_set(Reg32.PF, parity(c[0], sz))

        if not cmp:
            vm.reg.set(0, c)

        name = 'sub' if sub else 'add'
        debug('{} {}, imm{}({})'.format('cmp' if cmp else name, [0, 'al', 'ax', 0, 'eax'][sz], sz * 8, b))

        return True

    @staticmethod
    def rm_imm(vm, _8bit_op, _8bit_imm, sub=False, cmp=False, carry=False) -> bool:
        sz = 1 if _8bit_op else vm.operand_size
        imm_sz = 1 if _8bit_imm else vm.operand_size

        assert sz >= imm_sz
        old_eip = vm.eip

        RM, R = vm.process_ModRM(sz, sz)

        if not sub:
            if (not carry) and (R[1] != 0):
                vm.eip = old_eip
                return False  # this is not ADD
            elif carry and (R[1] != 2):
                vm.eip = old_eip
                return False  # this is not ADC
        elif sub:
            if not carry:
                if not cmp and (R[1] != 5):
                    vm.eip = old_eip
                    return False  # this is not SUB
                elif cmp and (R[1] != 7):
                    vm.eip = old_eip
                    return False  # this is not CMP
            else:
                if R[1] != 3:
                    vm.eip = old_eip
                    return False  # this is not SBB

        b = vm.mem.get(vm.eip, imm_sz)
        vm.eip += imm_sz
        b = sign_extend(b, sz)
        b = to_int(b)

        if carry:
            b += vm.reg.eflags_get(Reg32.CF)

        type, loc, _ = RM

        a = to_int((vm.mem if type else vm.reg).get(loc, sz))
        c = a + (b if not sub else MAXVALS[sz] + 1 - b)

        sign_a = (a >> (sz * 8 - 1)) & 1
        sign_b = (b >> (sz * 8 - 1)) & 1
        sign_c = (c >> (sz * 8 - 1)) & 1

        if not sub:
            vm.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.CF, c > MAXVALS[sz])
            vm.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
        else:
            vm.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.CF, b > a)
            vm.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))

        vm.reg.eflags_set(Reg32.SF, sign_c)

        c &= MAXVALS[sz]

        vm.reg.eflags_set(Reg32.ZF, c == 0)

        c = c.to_bytes(sz, byteorder)

        vm.reg.eflags_set(Reg32.PF, parity(c[0], sz))

        if not cmp:
            (vm.mem if type else vm.reg).set(loc, c)

        name = 'sub' if sub else 'add'
        debug('{0} {5}{1}({2}),imm{3}({4})'.format('cmp' if cmp else name, sz * 8, loc, imm_sz * 8, b, ('m' if type else 'r')))

        return True

    @staticmethod
    def rm_r(vm, _8bit, sub=False, cmp=False, carry=False) -> True:
        sz = 1 if _8bit else vm.operand_size

        RM, R = vm.process_ModRM(sz, sz)

        type, loc, _ = RM

        a = to_int((vm.mem if type else vm.reg).get(loc, sz))
        b = to_int(vm.reg.get(R[1], sz))

        if carry:
            b += vm.reg.eflags_get(Reg32.CF)

        c = a + (b if not sub else MAXVALS[sz] + 1 - b)

        sign_a = (a >> (sz * 8 - 1)) & 1
        sign_b = (b >> (sz * 8 - 1)) & 1
        sign_c = (c >> (sz * 8 - 1)) & 1

        if not sub:
            vm.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.CF, c > MAXVALS[sz])
            vm.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
        else:
            vm.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.CF, b > a)
            vm.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))

        vm.reg.eflags_set(Reg32.SF, sign_c)

        c &= MAXVALS[sz]

        vm.reg.eflags_set(Reg32.ZF, c == 0)

        c = c.to_bytes(sz, byteorder)

        vm.reg.eflags_set(Reg32.PF, parity(c[0], sz))

        if not cmp:
            (vm.mem if type else vm.reg).set(loc, c)

        name = 'sub' if sub else 'add'
        debug('{0} {4}{1}({2}),r{1}({3})'.format('cmp' if cmp else name, sz * 8, loc, R[1], ('m' if type else '_r')))

        return True

    @staticmethod
    def r_rm(vm, _8bit, sub=False, cmp=False, carry=False) -> True:
        sz = 1 if _8bit else vm.operand_size

        RM, R = vm.process_ModRM(sz, sz)

        type, loc, _ = RM

        a = to_int((vm.mem if type else vm.reg).get(loc, sz))
        b = to_int(vm.reg.get(R[1], sz))

        if carry:
            b += vm.reg.eflags_get(Reg32.CF)

        c = a + (b if not sub else MAXVALS[sz] + 1 - b)

        sign_a = (a >> (sz * 8 - 1)) & 1
        sign_b = (b >> (sz * 8 - 1)) & 1
        sign_c = (c >> (sz * 8 - 1)) & 1

        if not sub:
            vm.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.CF, c > MAXVALS[sz])
            vm.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
        else:
            vm.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.CF, b > a)
            vm.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))

        vm.reg.eflags_set(Reg32.SF, sign_c)

        c &= MAXVALS[sz]

        vm.reg.eflags_set(Reg32.ZF, c == 0)

        c = c.to_bytes(sz, byteorder)

        vm.reg.eflags_set(Reg32.PF, parity(c[0], sz))

        if not cmp:
            vm.reg.set(R[1], c)

        name = 'sub' if sub else 'add'
        debug('{0} r{1}({2}),{4}{1}({3})'.format('cmp' if cmp else name, sz * 8, R[1], loc, ('m' if type else '_r')))

        return True


####################
# AND / OR / XOR / TEST
####################
class BITWISE:
    """
    Perform a bitwise operation.
    Flags:
        OF, CF cleared
        SF, ZF, PF set according to the result
        AF undefined

    Operation: c <- a [op] b

    :param test: whether the instruction to be executed is TEST
    """
    @staticmethod
    def r_imm(vm, _8bit, operation, test=False) -> True:
        sz = 1 if _8bit else vm.operand_size
        b = vm.mem.get(vm.eip, sz)
        vm.eip += sz
        b = to_int(b)

        a = to_int(vm.reg.get(0, sz))

        vm.reg.eflags_set(Reg32.OF, 0)
        vm.reg.eflags_set(Reg32.CF, 0)

        c = operation(a, b)

        vm.reg.eflags_set(Reg32.SF, (c >> (sz * 8 - 1)) & 1)

        c &= MAXVALS[sz]

        vm.reg.eflags_set(Reg32.ZF, c == 0)

        c = c.to_bytes(sz, byteorder)

        vm.reg.eflags_set(Reg32.PF, parity(c[0], sz))

        if not test:
            name = operation.__name__
            vm.reg.set(0, c)
        else:
            name = 'test'

        debug('{} {}, imm{}({})'.format(name, [0, 'al', 'ax', 0, 'eax'][sz], sz * 8, b))

        return True

    @staticmethod
    def rm_imm(vm, _8bit, _8bit_imm, operation, test=False) -> bool:
        sz = 1 if _8bit else vm.operand_size
        imm_sz = 1 if _8bit_imm else vm.operand_size
        old_eip = vm.eip

        RM, R = vm.process_ModRM(sz, sz)

        if (operation == operator.and_):
            if (not test) and (R[1] != 4):
                vm.eip = old_eip
                return False  # this is not AND
            elif test and (R[1] != 0):
                vm.eip = old_eip
                return False  # this is not TEST
        elif (operation == operator.or_) and (R[1] != 1):
            vm.eip = old_eip
            return False  # this is not OR
        elif (operation == operator.xor) and (R[1] != 6):
            vm.eip = old_eip
            return False  # this is not XOR

        b = vm.mem.get(vm.eip, imm_sz)
        vm.eip += imm_sz
        b = sign_extend(b, sz)
        b = to_int(b)

        type, loc, _ = RM

        vm.reg.eflags_set(Reg32.OF, 0)
        vm.reg.eflags_set(Reg32.CF, 0)

        a = to_int((vm.mem if type else vm.reg).get(loc, sz))
        c = operation(a, b)

        vm.reg.eflags_set(Reg32.SF, (c >> (sz * 8 - 1)) & 1)

        c &= MAXVALS[sz]

        vm.reg.eflags_set(Reg32.ZF, c == 0)

        c = c.to_bytes(sz, byteorder)

        vm.reg.eflags_set(Reg32.PF, parity(c[0], sz))

        if not test:
            name = operation.__name__
            (vm.mem if type else vm.reg).set(loc, c)
        else:
            name = 'test'

        debug('{0} {5}{1}({2}),imm{3}({4})'.format(name, sz * 8, loc, imm_sz * 8, b, ('m' if type else 'r')))

        return True

    @staticmethod
    def rm_r(vm, _8bit, operation, test=False) -> True:
        sz = 1 if _8bit else vm.operand_size
        RM, R = vm.process_ModRM(sz, sz)

        type, loc, _ = RM

        vm.reg.eflags_set(Reg32.OF, 0)
        vm.reg.eflags_set(Reg32.CF, 0)

        a = to_int((vm.mem if type else vm.reg).get(loc, sz))
        b = to_int(vm.reg.get(R[1], sz))

        c = operation(a, b)

        vm.reg.eflags_set(Reg32.SF, (c >> (sz * 8 - 1)) & 1)

        c &= MAXVALS[sz]

        vm.reg.eflags_set(Reg32.ZF, c == 0)

        c = c.to_bytes(sz, byteorder)

        vm.reg.eflags_set(Reg32.PF, parity(c[0], sz))

        if not test:
            name = operation.__name__
            (vm.mem if type else vm.reg).set(loc, c)
        else:
            name = 'test'

        debug('{0} {4}{1}({2}),r{1}({3})'.format(name, sz * 8, loc, R[1], ('m' if type else '_r')))

        return True

    @staticmethod
    def r_rm(vm, _8bit, operation, test=False) -> True:
        sz = 1 if _8bit else vm.operand_size
        RM, R = vm.process_ModRM(sz, sz)

        type, loc, _ = RM

        vm.reg.eflags_set(Reg32.OF, 0)
        vm.reg.eflags_set(Reg32.CF, 0)

        a = to_int((vm.mem if type else vm.reg).get(loc, sz))
        b = to_int(vm.reg.get(R[1], sz))

        c = operation(a, b)

        vm.reg.eflags_set(Reg32.SF, (c >> (sz * 8 - 1)) & 1)

        c &= MAXVALS[sz]

        vm.reg.eflags_set(Reg32.ZF, c == 0)

        c = c.to_bytes(sz, byteorder)

        vm.reg.eflags_set(Reg32.PF, parity(c[0], sz))

        if not test:
            name = operation.__name__
            vm.reg.set(R[1], c)
        else:
            name = 'test'

        debug('{0} r{1}({2}),{4}{1}({3})'.format(name, sz * 8, R[1], loc, ('m' if type else '_r')))

        return True


####################
# NEG / NOT
####################
class NEGNOT:
    """
    NEG: two's complement negate
    Flags:
        CF flag set to 0 if the source operand is 0; otherwise it is set to 1.
        OF (!), SF, ZF, AF(!), and PF flags are set according to the result.

    NOT: one's complement negation  (reverses bits)
    Flags:
        None affected
    """

    @staticmethod
    def operation_not(a, off):
        return MAXVALS[off] - a

    @staticmethod
    def operation_neg(a, off):
        return NEGNOT.operation_not(a, off) + 1

    @staticmethod
    def rm(vm, _8bit, operation) -> bool:
        sz = 1 if _8bit else vm.operand_size
        old_eip = vm.eip

        RM, R = vm.process_ModRM(sz, sz)

        if operation == 0:  # NEG
            if R[1] != 3:
                vm.eip = old_eip
                return False  # this is not NEG
            operation = NEGNOT.operation_neg
        elif operation == 1:  # NOT
            if R[1] != 2:
                vm.eip = old_eip
                return False  # this is not NOT
            operation = NEGNOT.operation_not
        else:
            raise ValueError("Invalid argument to __negnot_rm: this is an error in the VM")

        type, loc, _ = RM

        a = to_int((vm.mem if type else vm.reg).get(loc, sz))
        if operation == NEGNOT.operation_neg:
            vm.reg.eflags_set(Reg32.CF, a != 0)

        b = operation(a, sz) & MAXVALS[sz]

        sign_b = (b >> (sz * 8 - 1)) & 1

        if operation == NEGNOT.operation_neg:
            vm.reg.eflags_set(Reg32.SF, sign_b)
            vm.reg.eflags_set(Reg32.ZF, b == 0)

        b = b.to_bytes(sz, byteorder)

        if operation == NEGNOT.operation_neg:
            vm.reg.eflags_set(Reg32.PF, parity(b[0], sz))

        vm.reg.set(loc, b)

        debug('{0} {3}{1}({2})'.format(operation.__name__, sz * 8, loc, ('m' if type else '_r')))

        return True
    

####################
# INC / DEC
####################
class INCDEC:
    """
    Increment or decrement r/m8/16/32 by 1

    Flags:
        CF not affected
        OF, SF, ZF, AF, PF set according to the result

    Operation: c <- a +/- 1

    :param dec: whether the instruction to be executed is DEC. If False, INC is executed.
    """
    @staticmethod
    def rm(vm, _8bit, dec=False) -> bool:
        sz = 1 if _8bit else vm.operand_size
        old_eip = vm.eip

        RM, R = vm.process_ModRM(sz, sz)

        if (not dec) and (R[1] != 0):
            vm.eip = old_eip
            return False  # this is not INC
        elif dec and (R[1] != 1):
            vm.eip = old_eip
            return False  # this is not DEC

        type, loc, _ = RM

        a = to_int((vm.mem if type else vm.reg).get(loc, sz))
        b = 1

        c = a + (b if not dec else MAXVALS[sz] - 1 + b)

        sign_a = (a >> (sz * 8 - 1)) & 1
        sign_b = (b >> (sz * 8 - 1)) & 1
        sign_c = (c >> (sz * 8 - 1)) & 1

        if not dec:
            vm.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
        else:
            vm.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))

        vm.reg.eflags_set(Reg32.SF, sign_c)

        c &= MAXVALS[sz]

        vm.reg.eflags_set(Reg32.ZF, c == 0)

        c = c.to_bytes(sz, byteorder)

        vm.reg.eflags_set(Reg32.PF, parity(c[0], sz))

        (vm.mem if type else vm.reg).set(loc, c)
        debug('{3} {0}{1}({2})'.format('m' if type else '_r', sz * 8, loc, 'dec' if dec else 'inc'))

        return True

    @staticmethod
    def r(vm, _8bit, dec=False) -> True:
        """
        [See `incdec_rm` for description].
        """
        sz = 1 if _8bit else vm.operand_size
        loc = vm.opcode & 0b111

        a = to_int(vm.reg.get(loc, sz))
        b = 1

        c = a + (b if not dec else MAXVALS[sz] - 1 + b)

        sign_a = (a >> (sz * 8 - 1)) & 1
        sign_b = (b >> (sz * 8 - 1)) & 1
        sign_c = (c >> (sz * 8 - 1)) & 1

        if not dec:
            vm.reg.eflags_set(Reg32.OF, (sign_a == sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.AF, ((a & 255) + (b & 255)) > MAXVALS[1])
        else:
            vm.reg.eflags_set(Reg32.OF, (sign_a != sign_b) and (sign_a != sign_c))
            vm.reg.eflags_set(Reg32.AF, (b & 255) > (a & 255))

        vm.reg.eflags_set(Reg32.SF, sign_c)

        c &= MAXVALS[sz]

        vm.reg.eflags_set(Reg32.ZF, c == 0)

        c = c.to_bytes(sz, byteorder)

        vm.reg.eflags_set(Reg32.PF, parity(c[0], sz))

        vm.reg.set(loc, c)
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


####################
# XCHG
####################
class XCHG:
    @staticmethod
    def eax_r(vm) -> True:
        sz = vm.operand_size
        loc = vm.opcode & 0b111

        if loc != 0:  # not EAX
            tmp = vm.reg.get(0, sz)
            vm.reg.set(0, vm.reg.get(loc, sz))
            vm.reg.set(loc, tmp)

        debug('xchg eax, r{}({})'.format(sz * 8, loc))
        return True

    @staticmethod
    def rm_r(vm, _8bit) -> True:
        sz = 1 if _8bit else vm.operand_size

        RM, R = vm.process_ModRM(sz, sz)
        type, loc, _ = RM

        if loc != R[1]:
            tmp = (vm.mem if type else vm.reg).get(loc, sz)
            (vm.mem if type else vm.reg).set(loc, vm.reg.get(R[1], sz))
            vm.reg.set(R[1], tmp)

        debug('xchg r{1}({2}),{0}{1}({3})'.format(('m' if type else '_r'), sz * 8, R[1], tmp))
        return True

####################
# CBW / CWDE
####################
def cbwcwde(self) -> True:
    self.reg.set(0, sign_extend(self.reg.get(0, self.operand_size // 2), self.operand_size))

    debug('cbw' if self.operand_size == 2 else 'cwde')
    return True


####################
# CMC
####################
def cmc(self) -> True:
    self.reg.eflags_set(Reg32.CF, not self.reg.eflags_get(Reg32.CF))

    debug('cmc')
    return True

####################
# MOVS
####################
def movs(self, _8bit) -> True:
    sz = 1 if _8bit else self.operand_size

    esi = to_int(self.reg.get(6, sz))
    edi = to_int(self.reg.get(7, sz))

    self.mem.set(esi, self.mem.get(edi, sz))

    if not self.reg.eflags_get(Reg32.DF):
        esi += sz
        edi += sz
    else:
        esi -= sz
        edi -= sz

    esi &= MAXVALS[sz]
    edi &= MAXVALS[sz]

    self.reg.set(6, esi.to_bytes(sz, byteorder))
    self.reg.set(7, edi.to_bytes(sz, byteorder))

    debug('mov{}'.format('s' if sz == 1 else ('w' if sz == 2 else 'd')))
    return True