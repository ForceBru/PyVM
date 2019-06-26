import itertools
import requests
import re
import csv

TOTAL_COMBINAIONS = (
    0x100 - 3 * 8 +
    3 * 8 * 0x100
)

TOTAL_COMBINAIONS = 6376


def generate_combinations():
    """
    Generates all valid combinations of the ModRM & SIB bytes.
    :return: generator
    """

    for ModRM in range(0x100):
        MOD = (ModRM & 0b11000000) >> 6
        # REG = (ModRM & 0b00111000) >> 3
        RM = (ModRM & 0b00000111)

        if RM == 0b100 and MOD != 0b11:
            for SIB in range(0x100):
                ret = [ModRM, SIB]

                # scale = (SIB & 0b11000000) >> 6
                # index = (SIB & 0b00111000) >> 3
                base = (SIB & 0b00000111)

                if base == 0b101 and MOD == 0b00:
                    ret += [255, 255, 255, 127]  # 2147483647

                if MOD == 0b01:
                    ret += [127]
                elif MOD == 0b10:
                    ret += [255, 255, 255, 127]  # 2147483647

                yield bytes(ret), True
        else:
            ret = [ModRM]

            if MOD == 0 and RM == 0b101:
                ret += [255, 255, 255, 127]  # 2147483647
            elif MOD == 0b01:
                ret += [127]
            elif MOD == 0b10:
                ret += [255, 255, 255, 127]  # 2147483647

            yield bytes(ret), False


def grouper(iterable, n):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=(b'', False))


def grouped_bytecode(n: int):
    """

    :param n: Number of items in a group
    :return:
    """

    for data in grouper(generate_combinations(), n):
        bytecode, need_SIB = itertools.tee(data)
        yield b''.join(b'\x89' + line for line, _ in bytecode if line), (sib for _, sib in need_SIB)


def disassemble(n: int):
    regex = re.compile('<pre>(.+)</pre>')

    URL = 'http://shell-storm.org/online/Online-Assembler-and-Disassembler'

    for group in grouped_bytecode(n):
        bytecode, need_SIB = group
        req = requests.get(
            URL,
            params={
                'opcodes': bytecode.hex(),
                'arch': 'x86-32',
                'endianness': 'little',
                'dis_with_raw': True,
                'dis_with_ins': True
            }
        )

        HTML = req.content.decode()

        pre = regex.search(HTML).group(1)
        assembly_lines = (line.strip() + '\n' for line in pre.split('</br>') if line.strip())

        yield from zip(assembly_lines, need_SIB)


def parse_assembly_line(
        data: tuple,
        line_regex=re.compile(r'([0-9a-fA-F ]+?)\s+mov(?:\s+dword\s+ptr)?\s+(.+)')
):

    line, needs_SIB = data
    m = line_regex.match(line)

    if m is None:
        raise ValueError(f'regex did not work!: {line!r}')

    bytes_hex, operands = m.groups()

    # get rid of leading '89' byte
    Hex = bytes_hex[3:].strip()
    RM, R = operands.split(',')

    return Hex, RM.strip(), R.strip(), needs_SIB


def generate_csv(fname: str, n: int = 300):
    parsed_assembly = map(parse_assembly_line, disassemble(n))

    print(f'Writing combinations to file {fname!r}')
    with open(fname, 'w') as Out:
        fields = ['hex', 'RM', 'R', 'needs_SIB']
        writer = csv.DictWriter(Out, fields)
        writer.writeheader()

        i = 0
        for i, data in enumerate(parsed_assembly, 1):
            assert len(data) == len(fields)
            writer.writerow(dict(zip(fields, data)))

            print(f'\r{i / TOTAL_COMBINAIONS:.3%} done', end='')

        assert i == TOTAL_COMBINAIONS
    print(f'\nCombinations written to file {fname!r}')


if __name__ == '__main__':
    generate_csv('ModRM_combinations.csv')
