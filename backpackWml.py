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
import random
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

def getNewForm():
    rv="""
<select name="w" title="When">
    <option value="fifteen">15 Minutes</option>
    <option value="nexthour">Next hour</option>
    <option value="later">Later</option>
    <option value="morning">Morning</option>
    <option value="afternoon">Afternoon</option>
    <option value="evening">Evening</option>
    <option value="coupledays">Couple Days</option>
    <option value="nextweek">Next Week</option>
</select><br/>
Message: <input type="text" name="m"/><br/>

<anchor title="Schedule">
    <go href="/cgi-bin/backpackWml.py?r=%(rnd)d" method="post">
        <postfield name="when" value="$(w)"/>
        <postfield name="msg" value="$(m)"/>
        <postfield name="action" value="add"/>
    </go>
</anchor>
""" % {'rnd': random.Random().randint(0,10000)}
    return rv

def doList(bp, fs):
    reminders=bp.getUpcomingReminders()
    out="Found %d reminders:<br/>" % (len(reminders))
    for ts, id, message in reminders:
        out += "<b>%s</b><br/>%s<br/>\n" % (time.ctime(ts), message)
    out+='<a href="#new">Add a Reminder</a>'

    sendContent(wml(card("reminders", "Reminder list", out)
        + card("new", "New Reminder", getNewForm())))

def doAdd(bp, fs):
    when=fs["when"].value
    msg=fs["msg"].value

    ts=bp.getRelativeTime(when)
    formattedTs=bp.formatTime(ts)

    bp.createReminder(msg, formattedTs)
    sendContent(wml(card("added", "Added Reminder",
        "Added a reminder for %s:  %s" % (time.ctime(ts), msg))))

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
