#!/usr/bin/python

from sys import argv
from pprint import PrettyPrinter
from ansi import *
from helper import *

# import file
filename = "CircuitCAM.cam"
if len(argv) > 1:
    filename = argv[1]

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

# parse file metadata
print "Skipping 168 bytes of metadata(?)..."
metaLength = 168
#metainfo = data[cursor:cursor+metaLength]
cursor += 168

# parse layer list
print "Parsing layer list..."
# 0x95 43
cursor += 2

layer = {}
for l in range(30):
    # 0x95 1B 02
    # or
    # 0x95 18 02
    layerMagic = data[cursor:cursor+3]
    if  layerMagic != "\x95\x1b\x02" \
    and layerMagic != "\x95\x17\x02" \
    and layerMagic != "\x95\x18\x02":
        break
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
raw_input("Hit return...");

# skip the spaces
while data[cursor] == '\x20':
    cursor += 1

# parse tool list
print "Parsing tool list..."
cursor = 0x1843

# 0x95 4D: Beginn der Werkzeuggruppen
# 0x95 4F: Beginn der Werkzeuggruppen

# 0x95 29: Werkzeuggruppe

# 0x95 1F: Werkzeugliste
# 0x95 2F: Werkzeugliste
# 0x95 30: Werkzeugliste
# 0x95 33: Werkzeugliste

# 0x95 27
# 0x95 07 } Werkzeug
# 0x95 08

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

    if data[cursor-1:cursor+3] == "\x20\x20\x20\x20":
        # four spaces mark the end of the tool section
        break

PrettyPrinter(indent=4).pprint(tools)
raw_input("Hit return...");

# something with units (?)
print "Skipping something with units..."
while data[cursor:cursor+2] != "\x95\x33" \
  and data[cursor:cursor+2] != "\x95\x34":
    cursor += 1
while data[cursor:cursor+3] != "\x95\x26\x03" \
  and data[cursor:cursor+3] != "\x95\x21\x03":
    cursor += 1

# tons of coordinates...
print "Parsing design..."

while data[cursor:cursor+3] == "\x95\x26\x03" \
   or data[cursor:cursor+3] == "\x95\x21\x03":
    begin = cursor

    # 0x95 26 03
    # or
    # 0x95 21 03
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
            radius = None
            if data[c-11:c-9] == "\x55\x00":
                # 2x values
                s = data[c-11:c+1]

            if data[c-16:c-14] == "\x55\x00":
                # 3x values
                s = data[c-16:c+1]
                radius = s[13:17]

            if s != None:
                x = s[3:7]
                print ANSI_FG_CYAN,
                for i in range(len(x)):
                    print "{0:#0{1}x}".format(ord(x[i]),4),
                print ANSI_FG_YELLOW + "X=" + ANSI_RESET + str(float32(x)),

                y = s[8:12]
                print ANSI_FG_CYAN,
                for i in range(len(y)):
                    print "{0:#0{1}x}".format(ord(y[i]),4),
                print ANSI_FG_YELLOW + "Y=" + ANSI_RESET + str(float32(y)),

                if radius != None:
                    print ANSI_FG_CYAN,
                    for i in range(len(radius)):
                        print "{0:#0{1}x}".format(ord(radius[i]),4),
                    print ANSI_FG_YELLOW + "R=" + ANSI_RESET + str(float32(radius)),

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

