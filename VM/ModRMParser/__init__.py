if __name__ == '__main__':
    import gen
    from ModRM_parsers import class_map

    f_comb = 'ModRM_combinations.csv'
    f_anal = 'ModRM_analysis.csv'
    f_map = 'ModRM_map.py'

    # gen.generate_combinations_csv(f_comb)
    gen.generate_analysis_csv(f_comb, f_anal)
    gen.generate_py_from_analysis(f_anal, f_map, class_map)
