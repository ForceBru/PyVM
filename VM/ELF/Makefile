.PHONY: all
all: samples/hello

CC = /Users/forcebru/Desktop/Test/TOOLCHAIN/usr/local/bin/clang
CFLAGS = -target i386-unknown-linux-gnu \
	-march=i386 \
	-ffreestanding \
	-fomit-frame-pointer \
	-fno-builtin \
	-nostdlib \
	-nostdinc \
	-Isrc

LDFLAGS = -fuse-ld=lld -Wl,-Ttext -Wl,0

samples/obj/syscalls.o: src/syscalls.c ; $(CC) $(CFLAGS) -c $< -o $@
samples/obj/libc.o: src/libc.c ; $(CC) $(CFLAGS) -c $< -o $@
samples/obj/entry.o: src/entry.c ; $(CC) $(CFLAGS) -c $< -o $@

samples/hello: samples/obj/entry.o samples/obj/syscalls.o samples/obj/libc.o src/hello.c ; $(CC) $(CFLAGS) $(LDFLAGS) $^ -o $@

clean: ; rm -f samples/obj/*.o samples/hello