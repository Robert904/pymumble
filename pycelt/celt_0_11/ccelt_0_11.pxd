cdef extern from "celt-0.11.1/libcelt/celt_types.h":
    ctypedef short celt_int16
    ctypedef int celt_int32
    ctypedef unsigned short celt_uint_16
    ctypedef unsigned int celt_uint_32

cdef extern from "celt-0.11.1/libcelt/celt.h":
    ctypedef struct CELTMode:
        pass
    ctypedef struct CELTEncoder:
        pass
    ctypedef struct CELTDecoder:
        pass

    ctypedef CELTMode* const_celtmode_ptr "const CELTMode*"
    ctypedef celt_int16* const_celt_int16_ptr "const celt_int16*"
    ctypedef float* const_float_ptr "const float*"
    ctypedef unsigned char* const_unsigned_char_ptr "const unsigned char*"
    ctypedef char* const_char_ptr "const char*"

    CELTMode *celt_mode_create(celt_int32 Fs, int frame_size, int* error)
    void celt_mode_destroy(CELTMode *mode)

    int celt_encoder_get_size(int channels)
    int celt_encoder_get_size_custom(const_celtmode_ptr mode, int channels)
    CELTEncoder *celt_encoder_create(int sampling_rate, int channels, int *error)
    CELTEncoder *celt_encoder_create_custom(const_celtmode_ptr mode, int channels, int *error)
    CELTEncoder *celt_encoder_init(CELTEncoder *st, int sampling_rate, int channels, int *error)
    CELTEncoder *celt_encoder_init_custom(CELTEncoder *st, const_celtmode_ptr mode, int channels, int *error)
    int celt_encoder_ctl(CELTEncoder * st, int request, ...)
    void celt_encoder_destroy(CELTEncoder *encoder)
    int celt_encode_float(CELTEncoder *st, const_float_ptr pcm, int frame_size, unsigned char *compressed, int maxCompressedBytes)
    int celt_encode(CELTEncoder *st, const_celt_int16_ptr pcm, int frame_size, unsigned char *compressed, int maxCompressedBytes)

    int celt_decoder_get_size(int channels)
    int celt_decoder_get_size_custom(const_celtmode_ptr mode, int channels)
    CELTDecoder *celt_decoder_create(int sampling_rate, int channels, int *error)
    CELTDecoder *celt_decoder_create_custom(const_celtmode_ptr mode, int channels, int *error)
    CELTDecoder *celt_decoder_init(CELTDecoder *st, int sampling_rate, int channels, int *error)
    CELTDecoder *celt_decoder_init_custom(CELTDecoder *st, const_celtmode_ptr mode, int channels, int *error)
    void celt_decoder_destroy(CELTDecoder *st)
    int celt_decode_float(CELTDecoder *st, const_unsigned_char_ptr data, int len, float *pcm, int frame_size)
    int celt_decode(CELTDecoder *st, const_unsigned_char_ptr data, int len, celt_int16 *pcm, int frame_size)
    int celt_decoder_ctl(CELTDecoder * st, int request, ...)
    const_char_ptr celt_strerror(int error)

    int CELT_SET_BITRATE_REQUEST