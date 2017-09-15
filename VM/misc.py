from .CPU import to_int

def process_ModRM(self, size1, size2):
    '''
		Assumes that 'self.eip' points to ModRM.
		
		Returns:
			(type, offset, size), (type, offset, size)
			type:
				0 - register
				1 - address
		'''
    ModRM = self.mem.get(self.eip, 1)[0]
    # ModRM_orig = ModRM
    self.eip += 1

    RM = ModRM & 0b111
    ModRM >>= 3

    REG = ModRM & 0b111
    ModRM >>= 3

    MOD = ModRM

    # ModRM_out = bin(ModRM_orig)[2:]
    # ModRM_out = '0' * (8 - len(ModRM_out)) + ModRM_out
    # print("ModR/M({}:{})".format(ModRM_out, hex(ModRM_orig)))

    if MOD == 0b11:
        return (0, RM, size1), (0, REG, size2)

    if RM == 0b100:  # there is a SIB
        SIB = self.mem.get(self.eip, 1)[0]
        self.eip += 1

        base = SIB & 0b111
        SIB >>= 3

        index = SIB & 0b111
        SIB >>= 3

        scale = SIB

        if base == 0b101:
            if index != 0b100:
                addr = to_int(self.reg.get(index, 4), True) * (1 << scale)
            else:
                addr = 0

            if MOD == 0:
                d32 = self.mem.get(self.eip, 4)
                self.eip += 4
                d32 = to_int(d32, True)
                addr += d32
            elif MOD == 1:
                d8 = self.mem.get(self.eip, 1)
                self.eip += 1
                d8 = to_int(d8, True)
                addr += d8 + self.reg.get(base, 4)  # EBP
            elif MOD == 2:
                d32 = self.mem.get(self.eip, 4)
                self.eip += 4
                d32 = to_int(d32, True)
                addr += d32 + self.reg.get(base, 4)  # EBP
            else:
                raise ValueError('Invalid MOD value')
        else:  # base != 0b101
            addr = to_int(self.reg.get(base, 4), True) + to_int(self.reg.get(index, 4), True) * (1 << scale)
    else:  # RM != 0b100
        if MOD == 0:
            if RM == 0b101:
                d32 = self.mem.get(self.eip, 4)
                self.eip += 4
                addr = to_int(d32, True)
            else:
                addr = to_int(self.reg.get(RM, 4), True)
        elif MOD == 1:
            addr = to_int(self.reg.get(RM, 4), True)

            d8 = self.mem.get(self.eip, 1)
            self.eip += 1
            d8 = to_int(d8, True)
            addr += d8
        elif MOD == 2:
            addr = to_int(self.reg.get(RM, 4), True)

            d32 = self.mem.get(self.eip, 4)
            self.eip += 4
            d32 = to_int(d32, True)
            addr += d32
        else:
            raise ValueError('This must not happen!')

    return (1, addr, size1), (0, REG, size2)
