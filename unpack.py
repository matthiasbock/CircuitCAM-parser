#!/usr/bin/python

from sys import argv
from pprint import PrettyPrinter
from ansi import *
from helper import *
from magic import *
from dom import *

# import file
filename = "CircuitCAM.cam"
if len(argv) > 1:
    filename = argv[1]

data = open(filename,'r').read()
cursor = 0

# layers
objectNames = {}

# DOM
dom = None

# pointer to currently parsed object in DOM
domCursor = dom


#
# Magic bytes indicate the type of the following data
#
magicName      = '\x01'  # only the name string follows
magicIdName    = '\x02'  # an ID and a name string follow
magicId        = '\x03'  # four bytes ID follow
magicPath      = '\x04'  # null-terminated string follows
magicTransform = '\x05'  # 1 byte follows
magicSInt8     = '\x07'
magicSInt16    = '\x08'
magicSInt64    = '\x1a'  # 8 bytes follow, more significant 4 bytes first, in both 4 byte blocks: little-endian
magicConfigRef = '\x23'  # 4 bytes follow, basically a 32-bit unsigned integer
magicUInt8     = '\x27'
magicUInt16    = '\x28'
magicUInt32    = '\x29'
magicFloat32   = '\x2a'  # 4 bytes, little-endian
magicUnknown1  = '\x0a'  # 4 bytes follow
magicUnknown2  = '\x25'  # 1 byte follows
magicUnknown3  = '\x47'  # 1 byte follow
magicBoolean   = '\x67'  # 1 byte follow, 0x00 or 0x01

#
# Functions for reading a data type
#
def readUInt8():
    global data, cursor
    b = data[cursor]
    cursor += 1
    return ord(b)

def readUInt16():
    global data, cursor
    i = uint16(data[cursor:cursor+2])
    cursor += 2
    return i

def readUInt32():
    global data, cursor
    i = uint32(data[cursor:cursor+4])
    cursor += 4
    return i

# TODO
def readSInt8():
    # maybe this needs change
    return readUInt8()

# TODO
def readSInt16():
    # maybe this needs conversion
    global data, cursor
    i = sint16(data[cursor:cursor+2])
    cursor += 2
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

def readBoolean():
    global data, cursor
    c = data[cursor]
    cursor += 1
    return c == '\x01'

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

def readIdName():
    global data, cursor, objectNames
    assert data[cursor] == magicIdName
    cursor += 1
    # object ID
    ID = readUInt32()
    # layer name as string
    name = readString()
    objectNames[ID] = name
    return ID, name

def readId():
    global data, cursor, objectNames
    assert data[cursor] == magicId
    cursor += 1
    return readUInt32()

def readConfigItem():
    global data, cursor
    id, name = readIdName()
    s2 = ""
    if not data[cursor] in "\x55\x95\x20":
        s2 = "::0x"
        # read another four bytes
        for i in range(4):
            s2 += '{:02X}'.format(ord(data[cursor]))
            cursor += 1
    return id, name+s2

def readConfigItemRef():
    return readId()

def readConfigRef():
    global data, cursor, objectNames
    assert data[cursor] == magicConfigRef
    cursor += 1
    r = readUInt32()
    return str(r)+" ("+objectNames[r]+")"

def readColor():
    global data, cursor
    assert data[cursor] == magicSInt8
    cursor += 1
    r = readUInt8()
    assert data[cursor] == magicSInt8
    cursor += 1
    g = readUInt8()
    assert data[cursor] == magicUInt8
    cursor += 1
    b = readUInt8()
    return r << 16 | g << 8 | b

def color2string(c):
    r = c & 0xFF0000
    g = c & 0x00FF00
    b = c & 0x0000FF
    return "#"+'{:02X}'.format(r)+'{:02X}'.format(g)+'{:02X}'.format(b)

def readOrder():
    global data, cursor
    assert data[cursor] == magicUInt8
    cursor += 1
    order = readUInt8()
    return order

def readFill():
    global data, cursor
    assert data[cursor] == magicUInt8
    cursor += 1
    fill = readUInt8()
    return fill

def readTrueWidth():
    global data, cursor
    assert data[cursor] == magicUInt8
    cursor += 1
    trueWidth = readUInt8()
    return trueWidth

def readScCoordinate():
    global data, cursor
    s = data[cursor:cursor+10]
    cursor += 10
    return "0x"+"-".join('{:02X}'.format(ord(a)) for a in s)

def readScScale():
    global data, cursor
    if data[cursor] != magicUnknown1:
        return "<arguments missing>"
    assert data[cursor] == magicUnknown1
    cursor += 1
    f = readFloat32()
    assert data[cursor] in [magicSInt8, magicUInt8]
    cursor += 1
    b = readUInt8()
    if data[cursor] in [magicSInt8, magicUInt8]:
        # read another byte and float
        cursor += 1
        b2 = readUInt8()
        assert data[cursor] == magicFloat32
        cursor += 1
        f2 = readFloat32()
        return "f,b:b,f="+str(f)+","+str(b)+":"+","+str(b2)+","+str(f2)
    else:
        return "f,b="+str(f)+","+str(b)

def readShapeType():
    global data, cursor
    assert data[cursor] == magicUInt8
    cursor += 1
    t = readUInt8()
    return str(t)

def readShapeParameter():
    global data, cursor
    assert data[cursor] == magicFloat32 \
        or data[cursor] == magicUnknown1
    readExtraFloat = False
    if data[cursor] == magicUnknown1:
        print "!",
        readExtraFloat = True
    cursor += 1

    f = readFloat32()
    if readExtraFloat:
        assert data[cursor] == magicFloat32
        cursor += 1
        f2 = readFloat32()
        return str(f)+","+str(f2)
    else:
        return str(f)

def readPtr():
    global data, cursor
    assert data[cursor] == magicUnknown1
    cursor += 1
    a = readFloat32()
    assert data[cursor] == magicFloat32
    cursor += 1
    b = readFloat32()
    if data[cursor] == magicFloat32:
        cursor += 1
        c = readFloat32()
        return "f,f,f="+str(a)+","+str(b)+","+str(c)
    else:
        return "f,f="+str(a)+","+str(b)

def readEndType():
    global data, cursor
    assert data[cursor] == magicUnknown2
    cursor += 1
    t = readUInt8()
    return str(t)

def readCornerType():
    global data, cursor
    assert data[cursor] == magicUnknown2
    cursor += 1
    t = readUInt8()
    return str(t)

def readPathWidth():
    global data, cursor
    assert data[cursor] == magicFloat32
    cursor += 1
    f = readFloat32()
    return str(f)

def readTransform():
    global data, cursor
    assert data[cursor] == magicTransform
    cursor += 1
    b = readUInt8()
    return str(b)

#
# captureInterval can have multiple layouts:
#  float,float,byte,byte,float
#  float,float,float,float
#  float,float
#
def readCaptureInterval():
    global data, cursor
    assert data[cursor] == magicUnknown1
    cursor += 1
    f1 = readFloat32()
    extraFloat = False
    if data[cursor] == magicUnknown1: # then captureInterval has four floats, otherwise only 3
        cursor += 1
        extraFloat = True
        fx = readFloat32()
    assert data[cursor] in [magicFloat32, magicUnknown1]
    cursor += 1
    f2 = readFloat32()
    if data[cursor] in "\x95\x55\x20":
        if extraFloat:
            return "f,f,f="+str(f1)+","+str(fx)+","+str(f2)
        return "f,f="+str(f1)+","+str(f2)
    # else:
    if not extraFloat:
        b1 = readUInt8()
        b2 = readUInt8()
    assert data[cursor] == magicFloat32
    cursor += 1
    f3 = readFloat32()
    if extraFloat:
        return "f,f,f,f="+str(f1)+","+str(fx)+","+str(f2)+","+str(f3)
    else:
        return "f,f,b,b,f="+str(f1)+","+str(f2)+","+hex(b1)+","+hex(b2)+","+str(f3)

def readMinDrawLength():
    global data, cursor
    assert data[cursor] == magicFloat32
    cursor += 1
    f = readFloat32()
    return str(f)

def readOverlap():
    global data, cursor
    assert data[cursor] == magicFloat32
    cursor += 1
    f = readFloat32()
    return str(f)

#
# e can have the following shapes:
#  0x07 XX 27 XX 67 XX
#  0x08 XX XX 27 XX 67 XX
#
def readE():
    global data, cursor
    assert data[cursor] in [magicSInt8, magicSInt16]
    t = data[cursor]
    cursor += 1
    if t == magicSInt8:
        v = readSInt8()
    elif t == magicSInt16:
        v = readSInt16()

    assert data[cursor] == magicUInt8
    cursor += 1
    u = readUInt8()

    assert data[cursor] == magicBoolean
    cursor += 1
    b = readBoolean()

    return str(v)+","+str(u)+","+str(b)

def readJobInsulate():
    return readIdName()

def readJobOutput():
    global data, cursor
    assert data[cursor] in [magicName, magicIdName]
    t = data[cursor]
    if t == magicName:
        cursor += 1
        return readString()
    elif t == magicIdName:
        return readIdName()

def readJobCommand():
    return readIdName()

def readJobInteger():
    global data, cursor
    assert data[cursor] == magicSInt8
    cursor += 1
    i1 = readSInt8()
    assert data[cursor] in [magicUInt8, magicUInt16, magicUInt32]
    t = data[cursor]
    cursor += 1
    if t == magicUInt8:
        i2 = readUInt8()
    elif t == magicUInt16:
        i2 = readUInt16()
    elif t == magicUInt32:
        i2 = readUInt32()
    return 'Nr.'+str(i1)+" = "+str(i2)

def readJobBlock():
    global data, cursor
    assert data[cursor] == magicUnknown3
    cursor += 1
    v = readUInt8()
    return str(v)

def readJobReal():
    global data, cursor
    assert data[cursor] == magicSInt8
    cursor += 1
    a = readSInt8()
    assert data[cursor] == magicFloat32
    cursor += 1
    f = readFloat32()
    return "Nr."+str(a)+" = "+str(f)

def readJobIdentifier():
    global data, cursor
    assert data[cursor] == magicSInt8
    cursor += 1
    a = readSInt8()
    s = readString()
    return "Nr."+str(a)+" = "+s

def readJobString():
    global data, cursor
    assert data[cursor] in [magicSInt8, magicSInt16]
    t = data[cursor]
    cursor += 1
    if t == magicSInt8:
        a = readSInt8()
    elif t == magicSInt16:
        a = readSInt16()
    s = readString()
    return str(a)+","+s

def readJobForm():
    global data, cursor
    assert data[cursor] == magicSInt8
    cursor += 1
    a = readSInt8()
    return str(a)

def readLevelObject():
    global data, cursor
    assert data[cursor] == magicId
    cursor += 1
    return readUInt32()

def createChildNode(name=None):
    global dom
    newNode = Node(name)
    if domCursor != None:
        newNode.setParent(domCursor)
        domCursor.appendChild(newNode)
    if dom == None:
        dom = newNode
    return newNode

#
# Begin parsing a block in the file
# begins at first byte after block start
#
def parseBlock():
    global data, cursor, objectNames, dom, domCursor
    j = ord(data[cursor])
    decoded = dictionary[j]
    #print hex(j)+"=>"+decoded,
    print decoded,
    cursor += 1

    # things are about to explode => debug output
    if domCursor == None:
        print dom

    if decoded == "CAM_V0":
        ID, name = readIdName()
        domCursor = createChildNode(decoded)
        domCursor.appendAttribute("ID", ID)
        domCursor.appendAttribute("name", name)

    elif decoded == "ScInfo" \
      or decoded == "displayAttributes" \
      or decoded == "configurations" \
      or decoded == "configsGerber" \
      or decoded == "configsSiebMeyer" \
      or decoded == "configsExcellon" \
      or decoded == "configsHpgl" \
      or decoded == "configsLpkfMillDrill" \
      or decoded == "configsDxf" \
      or decoded == "configHeader" \
      or decoded == "configItemHeader" \
      or decoded == "levels" \
      or decoded == "flashAttribute" \
      or decoded == "drawAttribute" \
      or decoded == "path" \
      or decoded == "rectangle" \
      or decoded == "flash" \
      or decoded == "circle" \
      or decoded == "curve" \
      or decoded == "closedCurve" \
      or decoded == "polygonCutOut" \
      or decoded == "polygon" \
      or decoded == "layouts" \
      or decoded == "jobs" \
      or decoded == "jobsInsulate" \
      or decoded == "jobsOutput" \
      or decoded == "jobsCommand" \
      or decoded == "jobHeader" \
      or decoded == "jobTask" \
      or decoded == "levelObjects":
        domCursor = createChildNode(decoded)

    elif decoded == "ScSerialNumber" \
      or decoded == "ScOrganization" \
      or decoded == "ScLocation" \
      or decoded == "ScUser" \
      or decoded == "ScTemplate" \
      or decoded == "comment":
        domCursor.appendAttribute(decoded, readString())

    elif decoded == "ScCoordinate":
        x = readScCoordinate()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "timeStamp":
        x = readTimeStamp()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "designLevel":
        ID, name = readIdName()
        domCursor = createChildNode(decoded)
        domCursor.appendAttribute("id", ID)
        domCursor.appendAttribute("name", name)

    elif decoded == "color":
        color = readColor()
        domCursor.appendAttribute(decoded, color2string(color))

    elif decoded == "order":
        x = readOrder()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "fill":
        x = readFill()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "trueWidth":
        print readTrueWidth(),

    elif decoded == "configGerber" \
      or decoded == "configSiebMeyer" \
      or decoded == "configExcellon" \
      or decoded == "configHpgl" \
      or decoded == "configLpkfMillDrill" \
      or decoded == "configDxf" \
      or decoded == "layout":
        ID, name = readIdName()
        domCursor = createChildNode(decoded)
        domCursor.appendAttribute("id", ID)
        domCursor.appendAttribute("name", name)

    elif decoded == "configItem":
        # configItem has a weird variant with +4 unknown bytes
        ID, name = readConfigItem()
        print str(ID)+","+name,
        domCursor = createChildNode(decoded)
        domCursor.appendAttribute("id", ID)
        domCursor.appendAttribute("name", name)

    elif decoded == "configItemRef":
        x = readConfigItemRef()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "configRef":
        x = readConfigRef()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "shapeType":
        x = readShapeType()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "shapeParameter":
        x = readShapeParameter()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "ptr":
        x = readPtr()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "endType":
        x = readEndType()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "cornerType":
        x = readCornerType()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "pathWidth":
        x = readPathWidth()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "captureInterval":
        x = readCaptureInterval()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "minDrawLength":
        x = readMinDrawLength()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "ScScale":
        x = readScScale()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "overlap":
        x = readOverlap()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "e":
        x = readE()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "jobInsulate":
        x = readJobInsulate()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "jobOutput":
        x = readJobOutput()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "jobCommand":
        x = readJobCommand()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "jobForm":
        x = readJobForm()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "jobBlock":
        x = readJobBlock()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "jobIdentifier":
        x = readJobIdentifier()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "jobInteger":
        x = readJobInteger()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "jobReal":
        x = readJobReal()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "jobString":
        x = readJobString()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "transform":
        x = readTransform()
        domCursor.appendAttribute(decoded, x)

    elif decoded == "levelObject":
        x = readLevelObject()
        domCursor.appendAttribute(decoded, x)

    else:
        print "unsupported block type encountered"
        exit()

#
# Parse all entries in the file
#
while cursor < len(data):
    assert data[cursor] in "\x55\x95\x20\xB5\x52"

    if data[cursor] == '\x95':
        # begin tag
        cursor += 1
        print "(",
        parseBlock()

    elif data[cursor] == '\x55':
        # begin attribute
        cursor += 1
        print ";",
        parseBlock()

    elif data[cursor] == '\x20':
        # end section
        cursor += 1
        if domCursor != None:
            domCursor = domCursor.getParent()
        print ")"

    elif data[cursor] == '\xb5':
        # no idea, what this is
        print "Encountered unrecognized byte sequence"
        cursor += 2

print dom
