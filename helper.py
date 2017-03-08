#!/usr/bin/python

from struct import unpack

#
# Interpret 4 bytes as little-endian 32-bit integer
#
def uint32(s):
    return unpack('<L', s)[0]

#
# Interpret 4 bytes as little-endian 32-bit float
#
def float32(s):
    return unpack('<f', s)[0]

def int32(s):
    return unpack('<i', s)[0]

def uint24(s):
    return unpack('<L', '\0'+s)[0]
