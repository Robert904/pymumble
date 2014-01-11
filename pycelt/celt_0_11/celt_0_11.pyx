cimport ccelt_0_11 as ccelt
cimport cpython
from libc.stdlib cimport malloc, free

from constants import CELT_OK

cdef class CeltEncoder:
    """
    Cython Celt 0.11 encoder class
    """
    cdef ccelt.CELTEncoder* _celtencoder
    cdef unsigned int samplerate
    cdef unsigned int channels
    cdef ccelt.celt_int32 bitrate
    cdef int framesize

    def __cinit__(self, samplerate, channels):
        self.samplerate = samplerate
        self.channels = channels
        self.framesize = 480
        self._celtencoder = ccelt.celt_encoder_create(samplerate, channels, NULL)
  
    def __dealloc__(self):
        if self._celtencoder is not NULL:
            ccelt.celt_encoder_destroy(self._celtencoder)
  
    def set_bitrate(self, bitrate):
        self.bitrate = bitrate
        ccelt.celt_encoder_ctl(self._celtencoder, ccelt.CELT_SET_BITRATE_REQUEST, self.bitrate)

    def encode(self, data, size):
        """encode one frame of PCM audio"""
        #cdef unsigned char *out = <unsigned char *>malloc(compressedsize + 10)
#TODO: Make the buffer size dynamic
        cdef unsigned char out[4096]
        cdef unsigned char* buffer = <unsigned char *>data

        cdef int len = ccelt.celt_encode(self._celtencoder, <ccelt.celt_int16 *>buffer, <int>(size/2/self.channels), <unsigned char *>out, <int>4096)

        if len <= 0:
            raise Exception("CELT 0.11 encoding error %i" % len)

        outBytes = (<unsigned char *>out)[:len]

        #free(out)
        return outBytes
        
cdef class CeltDecoder:
    """
    Celt 0.11 decoder class
    """
    cdef ccelt.CELTDecoder* _celtdecoder
    cdef unsigned int samplerate
    cdef unsigned int channels
    cdef short *pcm_buffer
    cdef int framesize
    
    def __cinit__(self, samplerate, channels):
        self.samplerate = samplerate
        self.channels = channels
        self.framesize = 480
        self._celtdecoder = ccelt.celt_decoder_create(samplerate, channels, NULL)
        self.pcm_buffer = <short *>malloc(self.samplerate * 120 / 1000 * self.channels * 2)
    
    def __dealloc__(self):
        if self._celtdecoder is not NULL:
            ccelt.celt_decoder_destroy(self._celtdecoder)
            
        free(self.pcm_buffer)
        
    def decode(self, data, size):
        """Decode one frame of compressed audio to PCM"""
        cdef unsigned char* buffer = <unsigned char *>data
        
        ret = ccelt.celt_decode(self._celtdecoder, buffer, <int>size, self.pcm_buffer, self.framesize)
        
        if ret != CELT_OK:
            raise Exception("CELT 0.11 decoding error %i" % ret)
        
        result = (<unsigned char *>self.pcm_buffer)[:self.framesize*2*self.channels]
        
        #free(pcm)
        return result
        
        