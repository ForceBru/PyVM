from .ModRM_parsers import class_map
from . import gen

def generate_ModRM_map(f_map: str):
    f_comb = 'ModRM_combinations.csv'
    f_anal = 'ModRM_analysis.csv'

    gen.generate_combinations_csv(f_comb)
    gen.generate_analysis_csv(f_comb, f_anal)
    gen.generate_py_from_analysis(f_anal, f_map, class_map)
