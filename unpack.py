#!/usr/bin/python

from helper import *

# import file
filename = "CircuitCAM.cam"

data = open(filename,'r').read()

# parse header
header = data[:0x1B]
print header

# parse keyword map
keywordMapLength = uint32(data[0x1B:0x1F])
print 'Parsing '+str(keywordMapLength)+' keywords...'

cursor = 0x1F
keywordMap = []
for i in range(keywordMapLength):
    terminator = data.find('\0', cursor)
    keywordMap.append( data[cursor:terminator] )
    cursor = terminator+1

print keywordMap
print str(len(keywordMap))
