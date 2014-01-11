
ifeq ($(PLATFORM), MINGW32)
	MOD_EXT = pyd
	ADD_FLAGS = -c mingw32
endif
ifeq ($(PLATFORM), UNIX)
	MOD_EXT = so
	ADD_FLAGS = 
endif

VERSION := 0.7.1
CELT := celt-$(VERSION)
MOD_NAME = celt_0_7

#-------------------------

$(MOD_NAME).$(MOD_EXT) : $(CELT)/libcelt/.libs/libcelt0.a $(MOD_NAME).pyx c$(MOD_NAME).pxd
	python setup.py build_ext --inplace $(ADD_FLAGS)

$(CELT)/libcelt/.libs/libcelt0.a : $(CELT)/Makefile
	cd $(CELT) && make

$(CELT)/Makefile : | $(CELT)
	cd $(CELT) && ./configure --disable-shared --enable-static

$(CELT) : $(CELT).tar.gz
	tar zxf $(CELT).tar.gz

$(CELT).tar.gz :
	echo "You must download and put here $(CELT).tar.gz file"

all : $(MOD_NAME).$(MOD_EXT)
.PHONY : all

clean :
	rm -r $(CELT) build $(MOD_NAME).c $(MOD_NAME).pyd