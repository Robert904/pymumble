# Relevant definitions from the libopus include files
#

#
# Types
#
from libc.stdint cimport int16_t, uint16_t, int32_t, uint32_t

cdef extern from "opus-1.1/include/opus_types.h":
    ctypedef int16_t opus_int16
    ctypedef uint16_t opus_uint16
    ctypedef int32_t opus_int32
    ctypedef uint32_t opus_uint32
    
    ctypedef int opus_int
    ctypedef long long opus_int64
    ctypedef signed char opus_int8
    ctypedef unsigned int opus_uint
    ctypedef unsigned long long opus_uint64
    ctypedef unsigned char opus_uint8

#
# Main definitions
#
cdef extern from "opus-1.1/include/opus.h":
    
# Encoder
    
    ctypedef struct OpusEncoder:
        pass

    OpusEncoder *opus_encoder_create(
                    opus_int32 Fs,
                    int channels,
                    int application,
                    int *error
                    )

    int opus_encoder_get_size(int channels)

    int opus_encoder_init(
                    OpusEncoder *st,
                    opus_int32 Fs,
                    int channels,
                    int application
                    )

    opus_int32 opus_encode(
                    OpusEncoder *st,
                    opus_int16 *pcm,
                    int frame_size,
                    unsigned char *data,
                    opus_int32 max_data_bytes
                    )

    opus_int32 opus_encode_float(
                    OpusEncoder *st,
                    float *pcm,
                    int frame_size,
                    unsigned char *data,
                    opus_int32 max_data_bytes
                    )

    void opus_encoder_destroy(OpusEncoder *st)

    int opus_encoder_ctl(OpusEncoder *st, int request, ...)

# Decoder
    
    ctypedef struct OpusDecoder:
        pass
        
    int opus_decoder_get_size(int channels)
    
    OpusDecoder *opus_decoder_create(
                    opus_int32 Fs,
                    int channels,
                    int *error
                    )

    int opus_decoder_init(
                    OpusDecoder *st,
                    opus_int32 Fs,
                    int channels
                    )
                    
    int opus_decode(
                    OpusDecoder *st,
                    unsigned char *data,
                    opus_int32 len,
                    opus_int16 *pcm,
                    int frame_size,
                    int decode_fec
                    )
    
    int opus_decode_float(
                    OpusDecoder *st,
                    unsigned char *data,
                    opus_int32 len,
                    float *pcm,
                    int frame_size,
                    int decode_fec
                    )
                    
    int opus_decoder_ctl(OpusDecoder *st, int request, ...)
    
    void opus_decoder_destroy(OpusDecoder *st)
    
    int opus_packet_parse(
                    unsigned char *data,
                    opus_int32 len,
                    unsigned char *out_toc,
                    unsigned char *frames[48],
                    opus_int16 size[48],
                    int *payload_offset
                    )
                    
    int opus_packet_get_bandwidth(unsigned char *data)
    
    int opus_packet_get_samples_per_frame(unsigned char *data, opus_int32 Fs)
    
    int opus_packet_get_nb_channels(unsigned char *data)
    
    int opus_packet_get_nb_frames(unsigned char packet[], opus_int32 len)
    
    int opus_packet_get_nb_samples(unsigned char packet[], opus_int32 len, opus_int32 Fs)
    
    int opus_decoder_get_nb_samples(OpusDecoder *dec, unsigned char packet[], opus_int32 len)
    
    void opus_pcm_soft_clip(float *pcm, int frame_size, int channels, float *softclip_mem)
    
# Repacketizer not implemented in pyopus

# multistream not implemented in pyopus 

#
# Constants definitions
#
cdef extern from "opus-1.1/include/opus_defines.h":
    int OPUS_OK
    int OPUS_BAD_ARG
    int OPUS_BUFFER_TOO_SMALL
    int OPUS_INTERNAL_ERROR
    int OPUS_INVALID_PACKET
    int OPUS_UNIMPLEMENTED
    int OPUS_INVALID_STATE
    int OPUS_ALLOC_FAIL

    int OPUS_SET_APPLICATION_REQUEST
    int OPUS_GET_APPLICATION_REQUEST
    int OPUS_SET_BITRATE_REQUEST
    int OPUS_GET_BITRATE_REQUEST
    int OPUS_SET_MAX_BANDWIDTH_REQUEST
    int OPUS_GET_MAX_BANDWIDTH_REQUEST
    int OPUS_SET_VBR_REQUEST
    int OPUS_GET_VBR_REQUEST
    int OPUS_SET_BANDWIDTH_REQUEST
    int OPUS_GET_BANDWIDTH_REQUEST
    int OPUS_SET_COMPLEXITY_REQUEST
    int OPUS_GET_COMPLEXITY_REQUEST
    int OPUS_SET_INBAND_FEC_REQUEST
    int OPUS_GET_INBAND_FEC_REQUEST
    int OPUS_SET_PACKET_LOSS_PERC_REQUEST
    int OPUS_GET_PACKET_LOSS_PERC_REQUEST
    int OPUS_SET_DTX_REQUEST
    int OPUS_GET_DTX_REQUEST
    int OPUS_SET_VBR_CONSTRAINT_REQUEST
    int OPUS_GET_VBR_CONSTRAINT_REQUEST
    int OPUS_SET_FORCE_CHANNELS_REQUEST
    int OPUS_GET_FORCE_CHANNELS_REQUEST
    int OPUS_SET_SIGNAL_REQUEST
    int OPUS_GET_SIGNAL_REQUEST
    int OPUS_GET_LOOKAHEAD_REQUEST
    int OPUS_GET_SAMPLE_RATE_REQUEST
    int OPUS_GET_FINAL_RANGE_REQUEST
    int OPUS_GET_PITCH_REQUEST
    int OPUS_SET_GAIN_REQUEST
    int OPUS_GET_GAIN_REQUEST
    int OPUS_SET_LSB_DEPTH_REQUEST
    int OPUS_GET_LSB_DEPTH_REQUEST
    int OPUS_GET_LAST_PACKET_DURATION_REQUEST
    int OPUS_SET_EXPERT_FRAME_DURATION_REQUEST
    int OPUS_GET_EXPERT_FRAME_DURATION_REQUEST
    int OPUS_SET_PREDICTION_DISABLED_REQUEST
    int OPUS_GET_PREDICTION_DISABLED_REQUEST
    
    int OPUS_AUTO
    int OPUS_BITRATE_MAX
    int OPUS_APPLICATION_VOIP
    int OPUS_APPLICATION_AUDIO
    int OPUS_APPLICATION_RESTRICTED_LOWDELAY
    
    int OPUS_SIGNAL_MUSIC
    int OPUS_SIGNAL_VOICE
    int OPUS_BANDWIDTH_NARROWBAND
    int OPUS_BANDWIDTH_MEDIUMBAND
    int OPUS_BANDWIDTH_WIDEBAND
    int OPUS_BANDWIDTH_SUPERWIDEBAND
    int OPUS_BANDWIDTH_FULLBAND
    
    int OPUS_FRAMESIZE_ARG
    int OPUS_FRAMESIZE_2_5_MS
    int OPUS_FRAMESIZE_5_MS
    int OPUS_FRAMESIZE_10_MS
    int OPUS_FRAMESIZE_20_MS
    int OPUS_FRAMESIZE_40_MS
    int OPUS_FRAMESIZE_60_MS
    
    int OPUS_RESET_STATE

#
# utilities
#

