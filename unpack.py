#!/usr/bin/python

from sys import argv
from pprint import PrettyPrinter
from ansi import *
from helper import *
from magic import *

# import file
filename = "CircuitCAM.cam"
if len(argv) > 1:
    filename = argv[1]

data = open(filename,'r').read()
cursor = 0


#
# Magic bytes indicate the type of the following data
#
magicID      = '\x02'
magicSInt8   = '\x07'
magicUInt8   = '\x27'
magicUInt64  = '\x1a'  # 8 bytes follow, more significant 4 bytes first, in both 4 byte blocks: little-endian
magicFloat32 = '\x2a'  # 4 bytes, little-endian
magicUnknown1 = '\x0a' # 4 bytes follow
magicUnknown2 = '\x25' # 1 byte follows

#
# Functions for reading a data type
#
def readByte():
    global data, cursor
    b = data[cursor]
    cursor += 1
    return ord(b)

def readUInt32():
    global data, cursor
    i = uint32(data[cursor:cursor+4])
    cursor += 4
    return i

def readFloat32():
    global data, cursor
    f = float32(data[cursor:cursor+4])
    cursor += 4
    return f

def readString():
    global data, cursor
    s = ""
    while data[cursor] != '\0':
        s += data[cursor]
        cursor += 1
    cursor += 1
    return s


# parse header
header = data[:0x16]
print "File magic: "+header
assert header == "BE == Binary EDIF File"
print

# parse keyword map
cursor = 0x1B
dictionaryLength = readUInt32()
print "Parsing dictionary with "+str(dictionaryLength)+" elements..."

dictionary = []
for i in range(dictionaryLength):
    terminator = data.find('\0', cursor)
    dictionary.append( data[cursor:terminator] )
    cursor = terminator+1

print dictionary
print

something = readUInt32()
print "Something: "+str(something)


#
# Functions to read CircuitCAM-specific fields in the file
#
def readTimeStamp():
    global data, cursor
    cursor += 13

def readDesignLevel():
    global data, cursor
    assert data[cursor] == magicID
    cursor += 1
    # object id
    id = readUInt32()
    # layer name as string
    name = readString()
    return "id="+str(id)+",name="+name

def readColor():
    global data, cursor
    assert data[cursor] == magicSInt8
    cursor += 1
    r = readByte()
    assert data[cursor] == magicSInt8
    cursor += 1
    g = readByte()
    assert data[cursor] == magicUInt8
    cursor += 1
    b = readByte()
    return "#"+'{:02X}'.format(r)+'{:02X}'.format(g)+'{:02X}'.format(b)

def readOrder():
    global data, cursor
    assert data[cursor] == magicUInt8
    cursor += 1
    order = readByte()
    return order

def readFill():
    global data, cursor
    assert data[cursor] == magicUInt8
    cursor += 1
    fill = readByte()
    return fill

def readTrueWidth():
    global data, cursor
    assert data[cursor] == magicUInt8
    cursor += 1
    trueWidth = readByte()
    return trueWidth

def readScCoordinate():
    global data, cursor
    s = data[cursor:cursor+10]
    cursor += 10
    return "0x"+"-".join('{:02X}'.format(ord(a)) for a in s)

def readConfigGerber():
    global data, cursor
    assert data[cursor] == magicID
    cursor += 1
    id = readUInt32()
    name = readString()
    return "id="+str(id)+",name="+name

def readConfigItem():
    global data, cursor
    assert data[cursor] == magicID
    cursor += 1
    id = readUInt32()
    name = readString()
    return "id="+str(id)+",name="+name

def readShapeType():
    global data, cursor
    assert data[cursor] == magicUInt8
    cursor += 1
    t = readByte()
    return str(t)

def readShapeParameter():
    global data, cursor
    assert data[cursor] == magicFloat32
    cursor += 1
    f = readFloat32()
    return str(f)

def readPtr():
    global data, cursor
    assert data[cursor] == magicUnknown1
    cursor += 1
    a = readFloat32()
    assert data[cursor] == magicFloat32
    cursor += 1
    b = readFloat32()
    assert data[cursor] == magicFloat32
    cursor += 1
    c = readFloat32()
    return str(a)+","+str(b)+","+str(c)

def readEndType():
    global data, cursor
    assert data[cursor] == magicUnknown2
    cursor += 1
    t = readByte()
    return str(t)

def readCornerType():
    global data, cursor
    assert data[cursor] == magicUnknown2
    cursor += 1
    t = readByte()
    return str(t)

def readPathWidth():
    global data, cursor
    assert data[cursor] == magicFloat32
    cursor += 1
    f = readFloat32()
    return str(f)

#
# Begin parsing a block in the file
# begins at first byte after block start
#
def parseBlock():
    global data, cursor
    j = ord(data[cursor])
    decoded = dictionary[j]
    print hex(j)+"=>"+decoded,
    cursor += 1

    if decoded == "CAM_V0":
        # expect one byte of unknown purpose + 4x zeroes
        cursor += 5
        # + 1x string
        name = readString()
        print name,

    elif decoded == "ScInfo":
        # has no arguments
        return

    elif decoded == "ScSerialNumber":
        ScSerialNumber = readString()
        print ScSerialNumber,

    elif decoded == "ScOrganization":
        ScOrganization = readString()
        print ScOrganization,

    elif decoded == "ScLocation":
        ScLocation = readString()
        print ScLocation,

    elif decoded == "ScUser":
        ScUser = readString()
        print ScUser,

    elif decoded == "timeStamp":
        timeStamp = readTimeStamp()
        print timeStamp,

    elif decoded == "ScTemplate":
        ScTemplate = readString()
        print ScTemplate,

    elif decoded == "comment":
        comment = readString()
        print comment,

    elif decoded == "levels":
        # no arguments
        return

    elif decoded == "designLevel":
        print readDesignLevel(),

    elif decoded == "displayAttributes":
        # no arguments
        return

    elif decoded == "color":
        print readColor(),

    elif decoded == "order":
        print readOrder(),

    elif decoded == "fill":
        print readFill(),

    elif decoded == "trueWidth":
        print readTrueWidth(),

    elif decoded == "configurations":
        # no arguments
        return

    elif decoded == "configsGerber":
        # no arguments
        return

    elif decoded == "configGerber":
        print readConfigGerber(),

    elif decoded == "configHeader":
        # no arguments
        return

    elif decoded == "ScCoordinate":
        print readScCoordinate(),

    elif decoded == "configItem":
        print readConfigItem(),

    elif decoded == "configItemHeader":
        # no arguments
        return

    elif decoded == "shapeType":
        print readShapeType(),

    elif decoded == "shapeParameter":
        print readShapeParameter(),

    elif decoded == "flashAttribute":
        # no arguments
        return

    elif decoded == "circle":
        # no arguments
        return

    elif decoded == "ptr":
        print readPtr(),

    elif decoded == "drawAttribute":
        # no arguments
        return

    elif decoded == "endType":
        print readEndType(),

    elif decoded == "cornerType":
        print readCornerType(),

    elif decoded == "pathWidth":
        print readPathWidth(),

    else:
        print "unsupported block type encountered"
        exit()

#
# Parse all entries in the file
#
for i in range(700):
    if data[cursor] == '\x55':
        # begin section?
        cursor += 1
        print ";",
        parseBlock()

    elif data[cursor] == '\x95':
        # begin section?
        cursor += 1
        print "(",
        parseBlock()

    elif data[cursor] == '\x20':
        # end section
        cursor += 1
        print ")"

print
