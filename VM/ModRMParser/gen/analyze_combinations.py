import csv
from ModRM_parsers import AddressC
from collections import namedtuple


class Register:
    names = 'eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi'
    type = AddressC.register

    def __init__(self, name: str):
        self.name = name
        self.number = self.names.index(self.name)

        assert self.number != -1

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'Register({self})'

    def __add__(self, other):
        if isinstance(other, Register):
            return Address(self, other, 1, None)
        if isinstance(other, RegisterScaled):
            return Address(self, other.reg, other.scale, None)
        if isinstance(other, int):
            return Address(self, None, None, other)

        raise ValueError(f'{self} + {other}')

    def __mul__(self, other):
        if isinstance(other, int):
            return RegisterScaled(self, other)

    def describe(self) -> dict:
        return {
            'type': int(self.type),
            'base': self.number,
            'index': None,
            'scale': None,
            'disp_size': None
        }


class RegisterScaled:
    def __init__(self, reg: Register, scale: int):
        self.reg, self.scale = reg, scale

    def __add__(self, other):
        if isinstance(other, int):
            return Address(None, self.reg, self.scale, other)

        raise ValueError(f'{self} + {other}')

    def __str__(self):
        return f'{self.reg} * {self.scale}'

    def __repr__(self):
        return f'Register({self})'


class Address(namedtuple('Address', 'base index scale disp')):
    @property
    def type(self):
        ret = AddressC.invalid

        if self.base is not None:
            ret |= AddressC.base
        if self.scale is not None and self.index is not None:
            if self.scale == 1:
                ret |= AddressC.index
            else:
                ret |= AddressC.index_scale
        if self.disp is not None:
            if self.disp.bit_length() + 1 == 32:
                ret |= AddressC.disp32
            elif self.disp.bit_length() + 1 == 8:
                ret |= AddressC.disp8
            else:
                raise ValueError(f'Invalid displacement size: {self.disp.bit_length()} bits for {self!r}')

        return ret

    def describe(self) -> dict:
        disp_size = ((self.disp.bit_length() + 1) // 4) if self.disp is not None else None

        return {
            'type': int(self.type),
            'base': self.base.number if self.base is not None else None,
            'index': self.index.number if self.index is not None else None,
            'scale': self.scale,
            'disp_size': disp_size
        }

    def __add__(self, other):
        if isinstance(other, int):
            assert self.disp is None
            return Address(self.base, self.index, self.scale, other)

    def __str__(self):
        if self.base is not None:
            ret = str(self.base)

            if self.index is not None and self.scale is not None:
                ret += f' + {self.index}'

                if self.scale > 1:
                    ret += f'*{self.scale}'

                if self.disp is not None:
                    ret += f' + 0x{self.disp:x}'
            elif self.disp is not None:
                ret += f' + 0x{self.disp:x}'
        elif self.index is not None and self.scale is not None:
            ret = f'{self.index}'

            if self.scale > 1:
                ret += f'*{self.scale}'

            if self.disp is not None:
                ret += f' + 0x{self.disp:x}'
        elif self.disp is not None:
            ret = f'0x{self.disp:x}'
        else:
            raise ValueError(f'Invalid address: {self!r}')

        return ret


def parse_address(line: str, locals: dict):
    ret = eval(line, locals)
    is_address = False

    if isinstance(ret, list):
        is_address = True
        ret, = ret
        if isinstance(ret, int):
            # just displacement
            ret = Address(None, None, None, ret)
        elif isinstance(ret, Register):
            ret = Address(ret, None, None, None)
    return ret, is_address


def generate_csv(fin: str, fout: str):
    namespace = dict(zip(Register.names, (Register(name) for name in Register.names)))
    fields = 'hex', 'sib', 'type', 'base', 'index', 'scale', 'disp_size', 'R'

    with open(fin) as In, open(fout, 'w') as Out:
        reader = csv.DictReader(In)
        writer = csv.DictWriter(Out, fields)

        writer.writeheader()

        address_types = set()
        for row in reader:
            RM = row['RM']
            addr, is_address = parse_address(RM, namespace)

            if is_address:
                address_types.add(addr.type)
                assert f'[{addr}]' == RM, f'{RM} != {addr} ({addr!r})'
            else:
                assert f'{addr}' == RM, f'{RM} != {addr} ({addr!r})'

            R, is_address = parse_address(row['R'], namespace)
            assert is_address is False

            writer.writerow({
                'hex': row['hex'],
                'sib': row['needs_SIB'],
                'R': R.number,
                **addr.describe()
            })

    return address_types


if __name__ == '__main__':
    print(generate_csv('ModRM_combinations.csv', 'ModRM_parsed.csv'))
