#!/usr/bin/env /usr/local/bin/python
"""
Backpack CGI.

Copyright (c) 2005  Dustin Sallings <dustin@spy.net>
"""
# arch-tag: 47697BE1-90E1-40AD-93F9-4D2D4E3F9BE5

import os
import sys
import cgi
import time
import ConfigParser

sys.path.append("/home/web/darcs/backpack")

import backpack

CONFIG_FILE="/usr/local/etc/backpack.conf"

HEADER="""<?xml version="1.0"?>
<!DOCTYPE wml PUBLIC
  "-//WAPFORUM//DTD WML 1.1//EN" "http://www.wapforum.org/DTD/wml_1.1.xml">
"""

# Get the config loaded
conf=ConfigParser.ConfigParser()
conf.read(CONFIG_FILE)

def sendContent(data):
    sys.stdout.write("Content-type: text/vnd.wap.wml\n")
    toSend=HEADER + data
    sys.stdout.write("Content-length: %d\n\n" % len(toSend))
    sys.stdout.write(toSend)

def wml(s):
    return "<wml>%s</wml>" % (s,)

def card(id, title, s):
    return """<card id="%(id)s" title="%(title)s"><p>%(s)s</p></card>""" % \
        {'id': id, 'title': title, 's': s}

def doList(bp, fs):
    reminders=bp.getUpcomingReminders()
    out=""
    for ts, id, message in reminders:
        out += "<b>%s</b><br/>%s<br/>" % (time.ctime(ts), message)

    sendContent(wml(card("reminders", "Reminder list", out)))

def doAdd(bp, fs):
    pass

def doDelete(bp, fs):
    pass

def handleException(tvt):
    """Print out any exception that may occur."""
    type, value, tb = tvt

    sendContent(wml(card("error", "Error",
        "<b>Got an error:</b><br/>  %s" % (value,))))

if __name__ == '__main__':
    fs=cgi.FieldStorage()
    bp=backpack.Backpack(conf.get("backpack", "url"),
        conf.get("backpack", "key"))

    funcs={"list": doList, "add": doAdd, "delete": doDelete}

    action=funcs[fs.getvalue("action", "list")]

    try:
        action(bp, fs)
    except:
        handleException(sys.exc_info())
