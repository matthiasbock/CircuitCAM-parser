#!/usr/bin/python
#
# Class to hold a CircuitCAM design tree
#

#
# Node attributes:
#  e.g. jobInteger Nr.14 = 1
#  => this.attributes["jobInteger"][14] = 1
#

#
# DOM node with attributes and child nodes
#
class Node:
    def __init__(this, name=None, parent=None):
        this.name = name
        this.setParent(parent)
        this.attributes = {}
        this.children = []

    def setName(this, name):
        this.name = name

    def setParent(this, parent):
        this.parent = parent
        this.indentLevel = 0
        if parent != None:
            this.indentLevel = parent.indentLevel + 1

    def getParent(this):
        return this.parent

    def appendChild(this, child):
        this.children.append(child)

    # add a top-level element to attributes (attribute is not an array)
    def appendAttribute(this, key, value):
        this.attributes[key] = value

    # append array element to attributes
    def appendAttributeElement(this, key, index, value):
        # make sure, array is initialized
        if not key in this.attributes.keys():
            this.attributes[key] = {}
        this.attributes[key][index] = value

    # convert attribute to string (for export)
    def attributeString(this, key):
        attribute = this.attributes[key]
        s = key + "="
        if type(attribute) is dict:
            s += "{" + ", ".join(str(subkey)+":"+str(attribute[subkey]) for subkey in attribute.keys()) + "}"
        elif type(attribute) is str:
            s += '"'+attribute+'"'
        elif type(attribute) is int:
            s += '"'+str(attribute)+'"'
        else:
            print "Error: Invalid attribute type"
        return s

    # return indentation string for this node
    def indentation(this):
        return "\t" * this.indentLevel

    # export node as string
    def xml(this):
        # indentation
        s = this.indentation() + "<"
        # tag name
        if this.name != None:
            s += this.name
            if len(this.attributes) > 0:
                s += ' '
        # attributes
        s += " ".join(this.attributeString(key) for key in this.attributes.keys())
        # child nodes
        if len(this.children) == 0:
            s += "/>\n"  # self-enclosing tag
        else:
            s += ">\n"
            # only other Node objects can be children
            s += " ".join([child.xml() for child in this.children])
            s += this.indentation() + "</"
            if this.name != None:
                s += this.name
            s += ">\n"
        return s

    def __str__(this):
        return this.xml()
