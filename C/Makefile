# Taken from: https://github.com/njlr/portable-cxx

####### BEGIN put your own clang, ar and ranlib here #######

CC=/Users/forcebru/Desktop/Test/TOOLCHAIN/usr/local/bin/clang
AR=/Users/forcebru/Desktop/Test/TOOLCHAIN/usr/local/bin/ar
RANLIB=/Users/forcebru/Desktop/Test/TOOLCHAIN/usr/local/bin/ranlib

####### END put your own clang, ar and ranlib here #######

SRC_DIR=src
BIN_DIR=bin

SRC_FILES=$(wildcard $(SRC_DIR)/*.c)
BIN_FILES=$(patsubst $(SRC_DIR)/%.c,$(BIN_DIR)/%.elf,$(SRC_FILES))

# the last four flags reduce binary size: http://ptspts.blogspot.com/2013/12/how-to-make-smaller-c-and-c-binaries.html
CFLAGS=-target i386-unknown-linux-elf -mno-avx -mno-sse -ffreestanding -fomit-frame-pointer -fno-builtin -nostdlib -nodefaultlibs -nostdinc -ffunction-sections -fdata-sections -fno-unroll-loops -fno-asynchronous-unwind-tables
LDFLAGS=-fuse-ld=lld

all: musl musl/root/lib/libgcc.a $(BIN_FILES)

bin/%.elf: src/%.c
	@echo "\tCompiling: " $< "->" $@
	$(CC) -std=c11 $(CFLAGS) $(LDFLAGS) -Wl,-Ttext -Wl,0 -static musl/root/lib/crt1.o $< --sysroot ./musl/root -isystem ./musl/root/include -L musl/root/lib -lc -lgcc -o $@ -Wall

# Get libgcc, because nothing will build without it.
libgcc-7-dev_7.4.0-8ubuntu1_i386.deb:
	curl http://fr.archive.ubuntu.com/ubuntu/pool/main/g/gcc-7/$@ --output $@

musl/root/lib/libgcc.a: libgcc-7-dev_7.4.0-8ubuntu1_i386.deb musl
	$(AR) -x $<
	rm debian-binary && rm control.tar.xz
	tar -xf data.tar.xz -m -C musl/root/lib --strip-components=6 ./usr/lib/gcc/i686-linux-gnu/7/libgcc.a ./usr/lib/gcc/i686-linux-gnu/7/libgcc_eh.a
	rm data.tar.xz

# Douwnload and build musl-libc.
musl.tar.xz:
	curl https://www.musl-libc.org/releases/musl-1.1.22.tar.gz --output $@

musl: musl.tar.xz
	mkdir -p $@
	tar -xf $< --directory $@ --strip-components=1
	ln -sf $(AR) $@/i386-unknown-linux-elf-ar
	ln -sf $(RANLIB) $@/i386-unknown-linux-elf-ranlib
	cd $@ && export CC=$(CC) CFLAGS="$(CFLAGS) $(LDFLAGS)" PATH=".:$$PATH" \
		&& ./configure --enable-debug --target=i386-unknown-linux-elf --prefix=root --disable-shared && make -j4 install

cleanall: clean
	rm -rf musl

clean:
	rm -f bin/*