from .ELF_structs import ELF32_Ehdr, ELF32_Shdr, ELF32_Phdr, ELF32_Sym
from .ELF_enums import EI_CLASS, EI_DATA, e_machine, e_type, p_type


__all__ = 'ELF32',


class ELF32:
    def __init__(self, fname: str):
        self.fname = fname
        self.file = open(self.fname, 'rb')
        self.hdr = ELF32_Ehdr(self.file)
        
        ident = self.hdr.e_ident
        
        assert (ident.EI_MAG0, ident.EI_MAG1, ident.EI_MAG2, ident.EI_MAG3) == (127, 69, 76, 70), f'Invalid header in file {self.fname!r}'
        
        assert ident.EI_CLASS == EI_CLASS.ELFCLASS32, f'64-bit architecture is not supported (file {self.fname!r})'
        assert ident.EI_DATA == EI_DATA.ELFDATA2LSB, f'Big endian is not supported (file {self.fname!r})'
        assert self.hdr.e_machine == e_machine.x86, f'Architecture {self.hdr.e_machine} is not supported (file {self.fname!r})'
        
        self.__phdrs = None
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        self.close()
        
    def close(self):
        self.file.close()
        
    @property
    def phdrs(self):
        if self.__phdrs is not None:
            return self.__phdrs
            
        self.file.seek(self.hdr.e_phoff)
        self.__phdrs = [ELF32_Phdr(self.file) for _ in range(self.hdr.e_phnum)]
        
        return self.__phdrs
