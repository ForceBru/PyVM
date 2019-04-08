import enums
from ELF_parser import *


__all__ = 'ELF32_Ehdr', 'ELF32_Phdr', 'ELF32_Shdr'

class ELF32_Ident(ELF_parser):
    EI_MAG0      : 'B'
    EI_MAG1      : 'B'
    EI_MAG2      : 'B'
    EI_MAG3      : 'B'
    EI_CLASS     : 'B' = enums.EI_CLASS
    EI_DATA      : 'B' = enums.EI_DATA
    EI_VERSION   : 'B'
    EI_OSABI     : 'B' = enums.EI_OSABI
    EI_ABIVERSION: 'B'
    EI_PAD       : '7s'


class ELF32_Ehdr(ELF_parser):
    e_ident    : ELF32_Ident
    e_type     : 'H' = enums.e_type
    e_machine  : 'H' = enums.e_machine
    e_version  : 'I'
    e_entry    : 'I'
    e_phoff    : 'I'
    e_shoff    : 'I'
    e_flags    : 'I'
    e_ehsize   : 'H'
    e_phentsize: 'H'
    e_phnum    : 'H'
    e_shentsize: 'H'
    e_shnum    : 'H'
    e_shstrndx : 'H'


class ELF32_Phdr(ELF_parser):
    p_type  : 'I' = enums.p_type
    p_offset: 'I'
    p_vaddr : 'I'
    p_paddr : 'I'
    p_filesz: 'I'
    p_memsz : 'I'
    p_flags : 'I'
    p_align : 'I'
    
    
class ELF32_Shdr(ELF_parser):
    sh_name     : 'I'
    sh_type     : 'I' = enums.sh_type
    sh_flags    : 'I' = enums.sh_flags
    sh_addr     : 'I'
    sh_offset   : 'I'
    sh_size     : 'I'
    sh_link     : 'I'
    sh_info     : 'I'
    sh_addralign: 'I'
    sh_entsize  : 'I'
