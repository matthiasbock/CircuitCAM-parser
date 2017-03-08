#!/usr/bin/python

from pprint import PrettyPrinter
from ansi import *
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
    print "Layer:  "+ANSI_FG_CYAN+str(layerNr)+" = "+layer[layerNr][1]+ANSI_RESET
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

    wrap = [2, 6]
    for c in range(begin,end):
        # end
        if data[c] == '\x20' \
        and data[c-1] != '\x55' \
        and data[c-4:c-2] != "\x55\x00" \
        and data[c-3:c-1] != "\x55\x00":
            print
            print "{0:#0{1}x}".format(ord(data[c]),4) + ANSI_FG_YELLOW + " // end" + ANSI_RESET
        else:
            print "{0:#0{1}x}".format(ord(data[c]),4),

        if data[c+1:c+3] == "\x55\x04":
            print ANSI_FG_YELLOW + "\n// begin something" + ANSI_RESET,

        # polygon parsing
        if data[c+1:c+3] == "\x55\x0b":
            print ANSI_FG_YELLOW + "\n// begin polygon" + ANSI_RESET,

        if data[c+1:c+3] == "\x55\x1f":
            print ANSI_FG_YELLOW + "\n// begin something" + ANSI_RESET,

        if data[c+1:c+3] == "\x55\x20":
            print ANSI_FG_YELLOW + "\n// begin something" + ANSI_RESET,

        if data[c+1:c+3] == "\x55\x24":
            print ANSI_FG_YELLOW + "\n// begin something" + ANSI_RESET,

        # coordinates parsing
        if (data[c+1] == '\x55' or data[c+1] == '\x20') \
        and data[c-3] != '\x55':
            s = None
            if data[c-11:c-9] == "\x55\x00":
                s = data[c-11:c+1]
            if data[c-16:c-14] == "\x55\x00":
                s = data[c-16:c+1]
            if s != None:
                x = s[3:6]
                y = s[8:11]
                print ANSI_FG_CYAN,
                for i in range(len(x)):
                    print "{0:#0{1}x}".format(ord(x[i]),4),
                print ANSI_FG_RED + str(uint24(x)) + ANSI_FG_CYAN,
                for i in range(len(y)):
                    print "{0:#0{1}x}".format(ord(y[i]),4),
                print ANSI_FG_RED + str(uint24(y)) + ANSI_RESET,

        if data[c+1:c+3] == "\x55\x00":
            print ANSI_FG_MAGENTA + "\n// coordinates" + ANSI_RESET,

        # circle/arc parsing
        if data[c+1:c+3] == "\x55\x05":
            print ANSI_FG_GREEN + "\n// circle/arc" + ANSI_RESET,

        # pretty-printing
        if data[c+1:c+3] == "\x55\x00" \
        or data[c+1:c+3] == "\x55\x01" \
        or data[c+1:c+3] == "\x55\x04" \
        or data[c+1:c+3] == "\x55\x05" \
        or data[c+1:c+3] == "\x55\x0b" \
        or data[c+1:c+3] == "\x55\x17" \
        or data[c+1:c+3] == "\x55\x1e" \
        or data[c+1:c+3] == "\x55\x1f" \
        or data[c+1:c+3] == "\x55\x18" \
        or data[c+1:c+3] == "\x55\x24":
            print

        try:
            if wrap.index(c-begin) > -1:
                print
        except:
            pass

    print
    print "Length: "+str(end-begin)
    raw_input("Hit return...");


cursor = 0x369DF
# 0x95 39 02

# three phases follow:
# * InsulateDefaultBottom
# * InsulateDefaultTop
# * InsulatePrevious

cursor = 0x36EAA
# 0x95 29 02

# many phases follow (?)

