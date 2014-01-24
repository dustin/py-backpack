#!/usr/bin/env /usr/local/bin/python
"""
WML support.

Copyright (c) 2005  Dustin Sallings <dustin@spy.net>
"""

import sys
import cgi
import ConfigParser

import backpack

CONFIG_FILE="/usr/local/etc/backpack.conf"

# Get the config loaded
conf=ConfigParser.ConfigParser()
conf.read(CONFIG_FILE)

HEADER="""<?xml version="1.0"?>
<!DOCTYPE wml PUBLIC
  "-//WAPFORUM//DTD WML 1.1//EN" "http://www.wapforum.org/DTD/wml_1.1.xml">
"""

def sendContent(data):
    """Send the content as wml"""
    sys.stdout.write("Content-type: text/vnd.wap.wml\n")
    toSend=HEADER + data
    sys.stdout.write("Content-length: %d\n\n" % len(toSend))
    sys.stdout.write(toSend)

def wml(s):
    """Wrap the contents in wml tags."""
    return "<wml>%s</wml>" % (s,)

def card(id, title, s):
    """Build a card by ID."""
    return """<card id="%(id)s" title="%(title)s"><p>%(s)s</p></card>""" % \
        {'id': id, 'title': title, 's': s}

def handleException(tvt):
    """Print out any exception that may occur."""
    type, value, tb = tvt

    sendContent(wml(card("error", "Error",
        "<b>Got an error:</b><br/>  %s" % (value,))))

def doCallback(funcs):
    """Execute the action."""
    fs=cgi.FieldStorage()
    bp=backpack.Backpack(conf.get("backpack", "url"),
        conf.get("backpack", "key"))

    action=funcs[fs.getvalue("action", "list")]

    try:
        action(bp, fs)
    except:
        handleException(sys.exc_info())
