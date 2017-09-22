CC=clang
LD=ld
ASM=nasm
ASMFLAGS=-f bin
CFLAGS=-S -O0 -mllvm --x86-asm-syntax=intel -fno-asynchronous-unwind-tables -fno-exceptions -fno-rtti -target i386-linux-gnu -nobuiltininc
LDFLAGS=--oformat binary -arch i386

C_SOURCES=pointers.c
ASM_SOURCES=$(C_SOURCES:.c=.s)

.PHONY: all clean

all: $(ASM_SOURCES)

clean:
	$(foreach var,$(ASM_SOURCES),rm $(var);)

%.s: %.c
	$(CC) $(CFLAGS) -o $(<:.c=.s) $<
