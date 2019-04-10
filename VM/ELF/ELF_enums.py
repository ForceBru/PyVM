from enum import Enum, Flag

EI_CLASS = Enum('EI_CLASS', 'ELFCLASSNONE ELFCLASS32 ELFCLASS64', start=0)
EI_DATA = Enum('EI_DATA', 'ELFDATANONE ELFDATA2LSB ELFDATA2MSB', start=0)

class EI_OSABI(Enum):
    ELFOSABI_NONE = 0 #Unspecified
    ELFOSABI_HPUX = 1 #Hewlett-Packard HP-UX
    ELFOSABI_NETBSD = 2 #NetBSD
    ELFOSABI_GNU = 3 #GNU
    ELFOSABI_SOLARIS = 6 #Sun Solaris
    ELFOSABI_AIX = 7 #AIX
    ELFOSABI_IRIX = 8 #IRIX
    ELFOSABI_FREEBSD = 9 #FreeBSD
    ELFOSABI_TRU64 = 10 #Compaq TRU64 UNIX
    ELFOSABI_MODESTO = 11 #Novell Modesto
    ELFOSABI_OPENBSD = 12 #Open BSD
    ELFOSABI_OPENVMS = 13 #Open VMS
    ELFOSABI_NSK = 14 #Hewlett-Packard Non-Stop Kernel
    ELFOSABI_AROS = 15 #Amiga Research OS
    ELFOSABI_FENIXOS = 16 #The FenixOS highly scalable multi-core OS
    ELFOSABI_CLOUDABI = 17 #Nuxi CloudABI
    ELFOSABI_OPENVOS = 18 #Stratus Technologies OpenVOS
    
    def _missing_(self):
        return self
        

class e_type(Enum):
    ET_NONE = 0x00
    ET_REL = 1
    ET_EXEC = 2
    ET_DYN = 3
    ET_CORE = 4
    ET_LOOS = 0xfe00
    ET_HIOS = 0xfeff
    ET_LOPROC = 0xff00
    ET_HIPROC = 0xffff

    
class e_machine(Enum):
    NONE = 0x00
    SPARC = 0x02
    x86 = 0x03
    MIPS = 0x08
    PowerPC = 0x14
    S390 = 0x16
    ARM = 0x28
    SuperH = 0x2A
    IA_64 = 0x32
    x86_64 = 0x3E
    AArch64 = 0xB7
    RISC_V = 0xF3
    

class p_type(Enum):
    PT_NULL	= 0
    PT_LOAD	= 0x00000001  # Loadable segment
    PT_DYNAMIC = 0x00000002	 # Dynamic linking information
    PT_INTERP = 0x00000003  # Interpreter information
    PT_NOTE = 0x00000004  # Auxiliary information
    PT_SHLIB = 0x00000005  # reserved
    PT_PHDR = 0x00000006  # segment containing program header table itself
    PT_LOOS = 0x60000000
    PT_HIOS = 0x6FFFFFFF
    PT_LOPROC = 0x70000000
    PT_HIPROC = 0x7FFFFFFF
    
    def _missing_(self):
        return self
        
    
class sh_type(Enum):
    SHT_NULL	= 0   # Null section
    SHT_PROGBITS= 1  # Program information
    SHT_SYMTAB	= 2   # Symbol table
    SHT_STRTAB	= 3   # String table
    SHT_RELA	= 4   # Relocation (w/ addend)
    SHT_HASH    = 5  # Symbol hash table
    SHT_DYNAMIC = 6  # Dynamic linking info
    SHT_NOTE    = 7
    SHT_NOBITS	= 8   # Not present in file
    SHT_REL		= 9   # Relocation (no addend)
    SHT_SHLIB   = 0x0A  # Reserved
    SHT_DYNSYM  = 0x0B  # Dynamic linker symbol table
    SHT_INIT_ARRAY = 0x0E  # Array of constructors
    SHT_FINI_ARRAY = 0x0F  # Array of destructors
    
    def _missing_(self):
        return self

        
class sh_flags(Flag):
    SHF_UNDEFINED = 0x0
    SHF_WRITE = 0x1
    SHF_ALLOC = 0x2
    SHF_EXECINSTR = 0x4
    SHF_MERGE = 0x10
    SHF_STRINGS = 0x20
    SHF_INFO_LINK = 0x40
    SHF_LINK_ORDER = 0x80
    SHF_OS_NONCONFORMING = 0x100
    SHF_GROUP = 0x200
    SHF_TLS = 0x400
    SHF_COMPRESSED = 0x800
    SHF_MASKOS = 0x0ff00000
    SHF_MASKPROC = 0xf0000000
    
    
class st_bind(Flag):
    STB_LOCAL = 0
    STB_GLOBAL = 1
    STB_WEAK = 2
    STB_LOOS = 10
    STB_HIOS = 12
    STB_LOPROC = 13
    STB_HIPROC = 15
    
    def _missing_(self):
        return self
        
class st_type(Flag):
    STT_NOTYPE = 0
    STT_OBJECT = 1
    STT_FUNC = 2
    STT_SECTION = 3
    STT_FILE = 4
    STT_COMMON = 5
    STT_TLS = 6
    STT_LOOS = 10
    STT_HIOS = 12
    STT_LOPROC = 13
    STT_HIPROC = 15
    
    def _missing_(self):
        return self
