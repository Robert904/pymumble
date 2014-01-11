cimport ccelt_0_7 as ccelt
cimport cpython
from libc.stdlib cimport malloc, free

from constants import CELT_OK

cdef class CeltEncoder:
    """
    Cython Celt 0.7 encoder class
    """
    cdef ccelt.CELTEncoder* _celtencoder
    cdef ccelt.CELTMode* _celtmode
    cdef unsigned int samplerate
    cdef unsigned int channels
    cdef ccelt.celt_int32 bitrate
    cdef int framesize

    def __cinit__(self, samplerate, channels):
        self.samplerate = samplerate
        self.channels = channels
        self.framesize = 480 # (10ms / 48000 Khz)
        self._celtmode = ccelt.celt_mode_create(samplerate, self.framesize, NULL)
        self._celtencoder = ccelt.celt_encoder_create(self._celtmode, channels, NULL)
  
    def __dealloc__(self):
        if self._celtencoder is not NULL:
            ccelt.celt_encoder_destroy(self._celtencoder)
            ccelt.celt_mode_destroy(self._celtmode)
  
    def set_bitrate(self, bitrate):
        self.bitrate = bitrate
        ccelt.celt_encoder_ctl(self._celtencoder, ccelt.CELT_SET_VBR_RATE_REQUEST, self.bitrate)

    def encode(self, data, compressedsize):
        """Encode one frame of PCM audio"""
        #cdef unsigned char *out = <unsigned char *>malloc(compressedsize + 10)
#TODO: Make the buffer size dynamic
        cdef unsigned char out[4096]
        cdef unsigned char* buffer = <unsigned char *>data

        cdef int len = ccelt.celt_encode(self._celtencoder, <short *>buffer, NULL, out, <int>compressedsize)

        if len < 0:
            raise Exception("CELT 0.7 encoding error %i" % len)
        
        outBytes = <unsigned char *>out

        #free(out)
        return outBytes[:len]
        
cdef class CeltDecoder:
    """
    Celt 0.7 decoder class
    """
    cdef ccelt.CELTDecoder* _celtdecoder
    cdef ccelt.CELTMode* _celtmode
    cdef unsigned int samplerate
    cdef unsigned int channels
    cdef ccelt.celt_int16 *pcm_buffer
    cdef int framesize
    
    def __cinit__(self, samplerate, channels):
        self.samplerate = samplerate
        self.channels = channels
        self.framesize = 480 # (10ms / 48000 Khz)
        self._celtmode = ccelt.celt_mode_create(samplerate, self.framesize, NULL)
        self._celtdecoder = ccelt.celt_decoder_create(self._celtmode, channels, NULL)
        self.pcm_buffer = <ccelt.celt_int16 *>malloc(self.samplerate * 120 / 1000 * self.channels * 2)
    
    def __dealloc__(self):
        if self._celtdecoder is not NULL:
            ccelt.celt_decoder_destroy(self._celtdecoder)
            ccelt.celt_mode_destroy(self._celtmode)
            
        free(self.pcm_buffer)
        
    def decode(self, data, size):
        """Decode one frame of encoded data to PCM"""
        cdef unsigned char* buffer = <unsigned char *>data
        
        ret = ccelt.celt_decode(self._celtdecoder, buffer, <int>size, self.pcm_buffer)
        
        if ret != CELT_OK:
            raise Exception("CELT 0.7 decoding error %i" % ret)
        
        result = (<unsigned char *>self.pcm_buffer)[:self.framesize*2*self.channels]
        
        #free(pcm)
        return result
        
        