# -*- coding: utf-8 -*-

from constants import *
import copus

class Opus:
    """Generic class for the Opus decoders and encoder"""
    def __init__(self, sampling_rate, channels):
        import struct
        
        self.sampling_rate = sampling_rate
        self.channels = channels
        self.signal_depth = 16
        
    def get_sampling_rate(self):
        return self.sampling_rate
    
    def set_sampling_rate(self, rate):
        self.rate = sampling_rate
        self._reset()
        
    def get_channels(self):
        return self.channels
    
    def set_channels(self, channels):
        self.channels = channels
        self._reset()
        
class OpusEncoder(Opus):
    def __init__(self, sampling_rate, channels, application=OPUS_APPLICATION_VOIP):
        Opus.__init__(self, sampling_rate, channels)
        self.application = application
        self.vbr = False
        
        self._reset()
        
    def _reset(self):
        self.encoder = copus.OpusEncoder(self.sampling_rate, self.channels, self.signal_depth, self.application)
        
    def set_bitrate(self, bitrate):
        self.encoder.set_bitrate(bitrate)
        
    def set_vbr(self, vbr):
        self.encoder.set_vbr(vbr)
        
    def encode(self, pcm):
        return self.encoder.encode(pcm, len(pcm))
        
class OpusDecoder(Opus):
    def __init__(self, rate, channels):
        Opus.__init__(self, rate, channels)
    
        self._reset()
        
    def _reset(self):
        self.decoder = copus.OpusDecoder(self.sampling_rate, self.channels, self.signal_depth)
        
    def decode(self, compressed):
        return self.decoder.decode(compressed)
    

        
        