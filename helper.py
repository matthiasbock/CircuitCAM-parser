#!/usr/bin/python

from struct import unpack

#
# Interpret 4 bytes as little-endian 32-bit integer
#
def uint32(s):
    return unpack('<L', s)[0]
