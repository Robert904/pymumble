cimport ccopus
cimport cpython
from libc.stdlib cimport malloc, free

from constants import OPUS_MAX_FRAMESIZE

cdef class OpusEncoder:
    """
    Cython Opus encoder class
    """
    cdef ccopus.OpusEncoder* encoder
    cdef ccopus.opus_int32 sampling_rate
    cdef int channels
    cdef ccopus.opus_int32 signal_depth
    cdef int application

    def __cinit__(self, sampling_rate, channels, signal_depth, application):
        self.sampling_rate = sampling_rate
        self.channels = channels
        self.application = application
        self.signal_depth = signal_depth
        
        self.encoder = ccopus.opus_encoder_create(sampling_rate, channels, application, NULL)
  
    def __dealloc__(self):
        if self.encoder is not NULL:
            ccopus.opus_encoder_destroy(self.encoder)
            
    def set_bitrate(self, bitrate):
        ccopus.opus_encoder_ctl(self.encoder, ccopus.OPUS_SET_BITRATE_REQUEST, <ccopus.opus_int32>bitrate) 
        
    def set_vbr(self, vbr):
        if vbr:
            ccopus.opus_encoder_ctl(self.encoder, ccopus.OPUS_SET_VBR_REQUEST, <ccopus.opus_int32>1)
        else:
            ccopus.opus_encoder_ctl(self.encoder, ccopus.OPUS_SET_VBR_REQUEST, <ccopus.opus_int32>0)

    def encode(self, data, size):
        """Encode one frame of PCM data"""
        #cdef unsigned char *out = <unsigned char *>malloc(compressedsize + 10)
#TODO: Make the buffer size dynamic
        cdef unsigned char out[9216]
        cdef unsigned char* buffer = <unsigned char *>data
        cdef int framesize = size * 8 // self.signal_depth // self.channels

        cdef int len = ccopus.opus_encode(self.encoder, <ccopus.opus_int16 *>buffer, framesize, out, <ccopus.opus_int32>9216)
        outBytes = <unsigned char *>out

        #free(out)
        return outBytes[:len]
        
cdef class OpusDecoder:
    """
    Cython Opus decoder class
    """
    cdef ccopus.OpusDecoder* decoder
    cdef ccopus.opus_int32 sampling_rate
    cdef int channels
    cdef ccopus.opus_int32 signal_depth
    cdef unsigned char *pcm_buffer
    cdef int pcm_buffer_samples
    
    def __cinit__(self, sampling_rate, channels, signal_depth):
        self.sampling_rate = sampling_rate
        self.channels = channels
        self.signal_depth = signal_depth

        self.decoder = ccopus.opus_decoder_create(sampling_rate, channels, NULL)

        self.pcm_buffer_samples = self.sampling_rate * OPUS_MAX_FRAMESIZE / 1000
        self.pcm_buffer = <unsigned char *>malloc(self.pcm_buffer_samples * self.channels * (self.signal_depth/8))
    
    def __dealloc__(self):
        if self.decoder is not NULL:
            ccopus.opus_decoder_destroy(self.decoder)
        free(self.pcm_buffer)
        
    def decode(self, data):
        """Decode one frame of encoded data to PCM"""
        cdef unsigned char* buffer = <unsigned char *>data
        
        ret = ccopus.opus_decode(self.decoder,
                                 buffer,
                                 <ccopus.opus_int32>len(data),
                                 <ccopus.opus_int16 *>self.pcm_buffer,
                                 self.pcm_buffer_samples,
                                 <int>0)
        
        if ret < 0:
            raise Exception("OPUS error %i" % ret)
        
        result = self.pcm_buffer
        
        return result[:ret*(self.signal_depth/8)*self.channels]
        
        