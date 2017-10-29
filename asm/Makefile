ASM=nasm
ASMFLAGS=-f bin -O0

SOURCES=$(sort $(wildcard test_*.s) $(wildcard c_*.s))
BINARIES=$(SOURCES:.s=.bin)

.PHONY: all clean

all: $(BINARIES)

clean:
	$(foreach var,$(BINARIES),rm bin/$(var);)

%.bin: %.s
	$(ASM) $(ASMFLAGS) -o bin/$(<:.s=.bin) $<
