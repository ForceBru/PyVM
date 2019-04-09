from ELF import ELF32_Ehdr, ELF32_Shdr, ELF32_Phdr, ELF32_Sym
from enums import EI_CLASS, EI_DATA, e_machine, p_type


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
        
        self.__sections = None
        self.__phdrs = None
        self.__dynsym = None
        self.__symtab = None
        self.__sections_contents = {}
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        self.close()
        
    def close(self):
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
        
    @property
    def phdrs(self):
        if self.__phdrs is not None:
            return self.__phdrs
            
        self.file.seek(self.hdr.e_phoff)
        self.__phdrs = [ELF32_Phdr(self.file) for _ in range(self.hdr.e_phnum)]
        
        return self.__phdrs
        
    @property
    def dynsym(self):
        if self.__dynsym is not None:
            return self.__dynsym
        
        try:
            sec_dynsym = self.sections['.dynsym']
            sec_dynstr = self.sections['.dynstr']
        except KeyError:
            return None
            
        self.file.seek(sec_dynsym.sh_offset)
        num = sec_dynsym.sh_size // sec_dynsym.sh_entsize
        
        dynsyms = [ELF32_Sym(self.file) for _ in range(num)]
        
        self.file.seek(sec_dynstr.sh_offset)
        names = self.file.read(sec_dynstr.sh_size)
        
        self.__dynsym = {
                names[sym.st_name:].split(b'\0', 1)[0].decode():
                    sym
                for sym in dynsyms
            }
        
        return self.__dynsym
        
    @property
    def symtab(self):
        if self.__symtab is not None:
            return self.__symtab
            
        try:
            sec_symtab = self.sections['.symtab']
            sec_strtab = self.sections['.strtab']
        except KeyError:
            return None
            
        self.file.seek(sec_symtab.sh_offset)
        num = sec_symtab.sh_size // sec_symtab.sh_entsize
        
        symbols = [ELF32_Sym(self.file) for _ in range(num)]
        
        self.file.seek(sec_strtab.sh_offset)
        names = self.file.read(sec_strtab.sh_size)
        
        self.__symtab = {
                names[sym.st_name:].split(b'\0', 1)[0].decode():
                    sym
                for sym in symbols
            }
        
        return self.__symtab

    def get_section_contents(self, section_name: str) -> bytes:
        try:
            return self.__sections_contents[section_name]
        except KeyError:
            section = self.sections[section_name]
            self.file.seek(section.sh_offset)
            
            self.__sections_contents[section_name] = self.file.read(section.sh_size)
            
        return self.__sections_contents[section_name]
        
    def load(self) -> bytes:
        ret = bytearray()
        
        for phdr in self.phdrs:
            if phdr.p_type != p_type.PT_LOAD:
                continue

            print(f'LOAD {phdr.p_memsz:10,d} bytes at address 0x{phdr.p_vaddr:09_x}')
            self.file.seek(phdr.p_offset)
                
            max_mem_offset = phdr.p_vaddr + phdr.p_memsz
                
            l = len(ret)
            if l < max_mem_offset:
                ret += bytearray(max_mem_offset - l)
                    
            ret[phdr.p_vaddr:phdr.p_vaddr + phdr.p_filesz] = self.file.read(phdr.p_filesz)
            ret[phdr.p_vaddr + phdr.p_filesz:phdr.p_vaddr + phdr.p_memsz] = bytearray(phdr.p_memsz - phdr.p_filesz)
                
        return ret
                


if __name__ == '__main__':
    import sys
    sys.path.insert(0, '../../')
    import VM
    
    hello = 'hello_world'
    bash  = 'elf-Linux-x86-bash'
    with ELF32(f'samples/{hello}') as ELF:
        #print(ELF.hdr)
        #print(ELF.sections.keys())
        #print(ELF.phdrs)
        #print(ELF.dynsym.keys())
        #print(ELF.symtab)
        #print(ELF.get_section_contents('.symtab'))
        print('Loading...')
        mem = ELF.load()
        print('Loaded!')
   
    sep = '-' * 40
    print('Allocating memory...')
    vm = VM.VM(len(mem) * 1.5)
    print(f'Allocated {vm.mem.bounds.stop:,} bytes!\nRunning...\n' + sep)
    vm.execute_bytes(mem, ELF.hdr.e_entry)
    print(sep)
