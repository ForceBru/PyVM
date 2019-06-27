from .Memory import Memory

reg_names = [
    [0, 'al', 'ax', 0, 'eax'],
    [0, 'cl', 'cx', 0, 'ecx'],
    [0, 'dl', 'dx', 0, 'edx'],
    [0, 'bl', 'bx', 0, 'ebx'],
    [0, 'ah', 'sp', 0, 'esp'],
    [0, 'ch', 'bp', 0, 'ebp'],
    [0, 'dh', 'si', 0, 'esi'],
    [0, 'bh', 'di', 0, 'edi'],
    ]


def debug_operand(operand: tuple, size: int) -> str:
    operand_type, operand_address = operand

    if isinstance(operand_type, Memory):
        return f'0x{operand_address:08x}'

    return reg_names[operand_address][size]


def debug_register_operand(operand: int, size: int) -> str:
    return reg_names[operand][size]
