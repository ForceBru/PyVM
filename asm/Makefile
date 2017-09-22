ASM=nasm
ASMFLAGS=-f bin

NAMES=test_jmp_int.s test_push_pop.s test_call_ret.s test_add_sub.s test_lea.s test_cmp_jcc.s c_pointers.s
BINARIES=$(NAMES:.s=.bin)

.PHONY: all clean

all: $(BINARIES)

clean:
	$(foreach var,$(BINARIES),rm $(var);)

%.bin: %.s
	$(ASM) $(ASMFLAGS) -o $(<:.s=.bin) $<
