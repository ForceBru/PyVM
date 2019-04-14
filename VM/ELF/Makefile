.PHONY: all
all: samples/hello samples/hello_dynamic

CC = /Users/forcebru/Desktop/Test/TOOLCHAIN/usr/local/bin/clang
AR = /Users/forcebru/Desktop/Test/TOOLCHAIN/usr/local/bin/ar
CFLAGS = -target i386-unknown-linux-gnu \
	-march=i386 \
	-ffreestanding \
	-fomit-frame-pointer \
	-fno-builtin \
	-nostdlib \
	-nostdinc \
	-Isrc

LDFLAGS = -fuse-ld=lld -Wl,-Ttext -Wl,0

samples/lib/libc.a: samples/obj/syscalls.o samples/obj/libc.o ; $(AR) rcsv $@ $^

samples/obj/syscalls.o: src/syscalls.c ; $(CC) $(CFLAGS) -c $< -o $@
samples/obj/libc.o: src/libc.c ; $(CC) $(CFLAGS) -c $< -o $@
samples/lib/entry.o: src/entry.c ; $(CC) $(CFLAGS) -c $< -o $@

samples/hello: samples/lib/entry.o src/hello.c samples/lib/libc.a ; $(CC) $(CFLAGS) $(LDFLAGS) $^ -o $@
samples/hello_dynamic: samples/lib/entry.o samples/lib/libc.a src/hello_dynamic.c ; $(CC) $(CFLAGS) $(LDFLAGS) $^ -o $@

clean: ; rm -f samples/obj/*.o samples/hello samples/hello_dynamic samples/lib/*.a