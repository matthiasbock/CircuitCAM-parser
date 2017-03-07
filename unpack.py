#!/usr/bin/python

from pprint import PrettyPrinter
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

# parse file metadata
print "Parsing metadata(?)..."
metainfo = data[cursor:0x4E7]

# parse layer list
print "Parsing layer list..."
cursor = 0x4E7
layer = {}
for l in range(30):
    # 0x95 1B 02
    layerMagic = data[cursor:cursor+3]
    cursor += 3

    layerNr = uint32(data[cursor:cursor+4])
    cursor += 4

    layerName = ""
    while data[cursor] != '\0':
        layerName += data[cursor]
        cursor += 1
    cursor += 1

    # info? setup?
    layerMeta = ""
    while data[cursor-2:cursor] != "\x20\x20":
        layerMeta += data[cursor]
        cursor += 1

    layer[layerNr] = [layerMagic, layerName, len(layerMeta), hex(len(layerMeta)), layerMeta]

PrettyPrinter(indent=4).pprint(layer)

# GerberDefault?
# SiebMeyerTools?
# ToolTutor?
# NcDrillDefault?

# parse tool list
print "Parsing tool list..."
cursor = 0x1843

tools = []
for i in range(81):
    # magic: 0x95 27 02 or 0x95 07 02
    toolMagic = data[cursor:cursor+3]
    cursor += 3

    toolNr = uint32(data[cursor:cursor+4])
    cursor += 4

    toolName = ""
    while data[cursor] != '\0':
        toolName += data[cursor]
        cursor += 1
    cursor += 1

    toolMeta = ""
    while data[cursor:cursor+2] != '\x20\x95' \
      and data[cursor:cursor+5] != '\x20\x20\x20\x20\xB5':
        toolMeta += data[cursor]
        cursor += 1
    cursor += 1

    tools.append( [toolMagic, toolNr, toolName, toolMeta] )

PrettyPrinter(indent=4).pprint(tools)

# something with units (?)

# tons of coordinates...
print "Parsing design..."
cursor = 0x314C

while data[cursor:cursor+3] == "\x95\x26\x03":
    begin = cursor

    # 0x95 26 03
    cursor += 3

    layerNr = uint32(data[cursor:cursor+4])
    cursor += 4
    print "Layer:  "+str(layerNr)+" ("+layer[layerNr][1]+")"
    print "Begin:  "+hex(begin)

#    for i in range(4):
#        drillHole = data[cursor:cursor+19]
#        for b in drillHole:
#            print "{0:#0{1}x}".format(ord(b),4),
#        print
#        cursor += 19

    while data[cursor:cursor+2] != "\x20\x95":
        cursor += 1

    # 0x20
    cursor += 1

    end = cursor
    print "End:    "+hex(end)
    print "Length: "+str(end-begin)


cursor = 0x369DF
# 0x95 39 02

# three phases follow:
# * InsulateDefaultBottom
# * InsulateDefaultTop
# * InsulatePrevious

cursor = 0x36EAA
# 0x95 29 02

# many phases follow (?)

