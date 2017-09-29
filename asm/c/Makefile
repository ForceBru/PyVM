ASM=nasm
ASMFLAGS=-f bin
CFLAGS=-S -O1 -mllvm --x86-asm-syntax=intel -fno-asynchronous-unwind-tables -fno-exceptions -fno-rtti -target i386-linux-gnu -nobuiltininc

C_SOURCES=$(sort $(wildcard *.c))
ASM_SOURCES=$(C_SOURCES:.c=.s)

.PHONY: all clean

all: $(ASM_SOURCES)

clean:
	$(foreach var,$(ASM_SOURCES),rm $(var);)

%.s: %.c
	$(CC) $(CFLAGS) -o $(<:.c=.s) $<
