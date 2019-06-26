import csv
from VM.ModRMParser.ModRM_map import ModRM_map


def parse_ModRM(bytecode: bytes):
    ModRM = bytecode[0]

    MOD = (ModRM & 0b11000000) >> 6
    RM = (ModRM & 0b00000111)

    if MOD == 0b11:
        return ModRM_map[ModRM].parse_raw(bytecode)

    if RM == 0b100:
        SIB = bytecode[1]
        return ModRM_map[ModRM][SIB].parse_raw(bytecode)

    return ModRM_map[ModRM].parse_raw(bytecode)


if __name__ == '__main__':
    correct_num, error, total = 0, 0, 6376

    with open('VM/ModRMParser/ModRM_combinations.csv') as f:
        reader = csv.DictReader(f)

        for i, line in enumerate(reader, 1):
            bytecode = bytes.fromhex(line['hex'])

            ret = parse_ModRM(bytecode)

            correct = line['RM'], line['R']

            if ret != correct:
                print(f'[{line["hex"]}] {ret} must be equal to {correct}')
                error += 1
            else:
                correct_num += 1

        assert i == total

        print(f'Correct: {correct_num / total:.2%}')
        print(f'Error: {error / total:.2%}')
