# -*- coding: utf-8 -*-

from constants import SUPPORTED_VERSIONS, SUPPORTED_BITSTREAMS
from errors import *
from constants import *

class Celt:
    """
    Generic class for the Celt decoders and encoder of different versions
    
    children classes must implement the reset() function that create the coder/decoder of the correct version
    """
    def __init__(self, rate, channels, version):
        import struct
        
        self.rate = rate
        self.channels = channels
        self.version = version
        
    def get_rate(self):
        return self.rate
    
    def set_rate(self, rate):
        self.rate = rate
        self._reset()
        
    def get_channels(self):
        return self.channels
    
    def set_channels(self, channels):
        self.channels = channels
        self._reset()
        
    def get_version(self):
        return self.version
    
    def set_version(self, version):
        """Set the version of Celt to use"""
        if ( version not in SUPPORTED_VERSIONS and
             version not in SUPPORTED_BITSTREAMS ):
            raise InvalidCeltVersionError(version)
        else:
            self.version = version

        self._reset()
        
class CeltEncoder(Celt):
    """Generic Celt encoder class"""
    def __init__(self, rate, channels, version="0.11"):
        Celt.__init__(self, rate, channels, version)
        
        self.set_version(version)
        
    def set_bitrate(self, bitrate):
        self.celt.set_bitrate(bitrate)
        
    def encode(self, pcm):
        """Encode one frame of PCM data"""
        return(self.celt.encode(pcm, len(pcm)))
        
    def _reset(self):
        """(re)Creates the encoder state object"""
        if self.version == "0.11" or self.version == SUPPORTED_VERSIONS["0.11"]:
            import celt_0_11
            self.celt = celt_0_11.CeltEncoder(self.rate, self.channels)
        elif self.version == "0.7" or self.version == SUPPORTED_VERSIONS["0.7"]:
            import celt_0_7
            self.celt = celt_0_7.CeltEncoder(self.rate, self.channels)
        
        
class CeltDecoder(Celt):
    """Generic Celt decoder class"""
    def __init__(self, rate, channels, version="0.11"):
        Celt.__init__(self, rate, channels, version)
        
        self.set_version(version)
        
    def decode(self, compressed):
        """Decode one frame of encoded date to PCM"""
        return(self.celt.decode(compressed, len(compressed)))

    def _reset(self):
        """(re)Creates the decoder state object"""
        if self.version == "0.11" or self.version == SUPPORTED_VERSIONS["0.11"]:
            import celt_0_11
            self.celt = celt_0_11.CeltDecoder(self.rate, self.channels)
        if self.version == "0.7" or self.version == SUPPORTED_VERSIONS["0.7"]:
            import celt_0_7
            self.celt = celt_0_7.CeltDecoder(self.rate, self.channels)
        
