import csv
import pprint

from .generate_combinations import TOTAL_COMBINAIONS


def generate_py_from_analysis(fin: str, fout: str, class_map: dict):
    ModRM_map = []

    print(f'Generating ModRM map from analysis ({fin!r})...')
    with open(fin) as In, open(fout, 'w') as Out:
        reader = csv.DictReader(In)

        i = 0
        for i, line in enumerate(reader, 1):
            needs_SIB = int(eval(line['sib']))
            bytecode = bytes.fromhex(line['hex'])
            _type = int(line['type'])

            base, index, scale, R = (
                int(line[name]) if line[name] else None
                for name in 'base index scale R'.split()
            )

            if needs_SIB:
                ModRM, SIB, *_ = bytecode

                if len(ModRM_map) == ModRM:
                    ModRM_map.append([])

                ModRM_map[ModRM].append(
                    class_map[_type](
                        base,
                        index,
                        scale,
                        2,  # because the displacement will be at index 2: [ModRM, SIB, disp...]
                        R,
                    )
                )
            else:
                ModRM, *_ = bytecode
                assert len(ModRM_map) == ModRM

                ModRM_map.append(
                    class_map[_type](
                        base, index, scale, 1, R
                    )
                )

            print(f'\r{i / TOTAL_COMBINAIONS:.3%} done', end='')

        assert i == TOTAL_COMBINAIONS
        Out.write('from .ModRM_parsers import *\n\n')
        Out.write('ModRM_map = ')
        pprint.pprint(ModRM_map, Out)

    print(f'\nModRM map written to {fout!r}')
