# PLATFORM may be "MINGW32" or "UNIX"
export PLATFORM = MINGW32
#export PLATFORM = UNIX
#-------------------------
ifeq ($(PLATFORM), MINGW32)
	MOD_EXT = pyd
endif
ifeq ($(PLATFORM), UNIX)
	MOD_EXT = so
endif


all : 0_7_mod 0_11_mod

0_7_mod: 0_7 
	cp celt_0_7/celt_0_7.$(MOD_EXT) ./

0_11_mod: 0_11
	cp celt_0_11/celt_0_11.$(MOD_EXT) ./

0_7 :
	$(MAKE) -C celt_0_7

0_11 :
	$(MAKE) -C celt_0_11

clean :
	$(MAKE) clean -C celt_0_7
	$(MAKE) clean -C celt_0_11
		
