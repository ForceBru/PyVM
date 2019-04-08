from ELF import ELF32_Ehdr, ELF32_Shdr
from enums import EI_CLASS, EI_DATA, e_machine


class ELF32:
    def __init__(self, fname: str):
        self.fname = fname
        self.file = open(self.fname, 'rb')
        self.hdr = ELF32_Ehdr(self.file)
        
        ident = self.hdr.e_ident
        
        assert ident.EI_MAG0 == 127\
        and ident.EI_MAG1 == 69\
        and ident.EI_MAG2 == 76\
        and ident.EI_MAG3 == 70, f'Invalid header in file {self.fname!r}'
        
        assert ident.EI_CLASS == EI_CLASS.ELFCLASS32, f'64-bit architecture is not supported (file {self.fname!r})'
        assert ident.EI_DATA == EI_DATA.ELFDATA2LSB, f'Big endian is not supported (file {self.fname!r})'
        assert self.hdr.e_machine == e_machine.x86, f'Architecture {self.hdr.e_machine} is not supported (file {self.fname!r})'
        
        self.__sections = None
        self.__sections_contents = {}
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        self.file.close()
        
    @property
    def sections(self):
        if self.__sections is None:
            self.file.seek(self.hdr.e_shoff)
            sections = [ELF32_Shdr(self.file) for _ in range(self.hdr.e_shnum)]
    
            shstrndx = sections[self.hdr.e_shstrndx]
            self.file.seek(shstrndx.sh_offset)
            names = self.file.read(shstrndx.sh_size)
        
            self.__sections = {
                names[section.sh_name:].split(b'\0', 1)[0].decode():
                    section
                for section in sections[1:]
            }
            
        return self.__sections

    def get_section_contents(self, section_name: str) -> bytes:
        try:
            return self.__sections_contents[section_name]
        except KeyError:
            section = self.sections[section_name]
            self.file.seek(section.sh_offset)
            
            self.__sections_contents[section_name] = self.file.read(section.sh_size)
            
        return self.__sections_contents[section_name]


if __name__ == '__main__':
    with ELF32('samples/hello_world') as ELF:
        print(ELF.hdr)
        print(ELF.sections)
