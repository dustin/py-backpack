#!/usr/bin/env /usr/local/bin/python
"""
Backpack CGI.

Copyright (c) 2005  Dustin Sallings <dustin@spy.net>
"""
# arch-tag: 47697BE1-90E1-40AD-93F9-4D2D4E3F9BE5

import os
import sys
import time
import random

sys.path.append("/home/web/darcs/backpack")

from wapsupport import *

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
    reminders=bp.reminder.list()
    out="Found %d reminders:<br/>" % (len(reminders))
    for ts, id, message in reminders:
        out += "<b>%s</b><br/>%s<br/>\n" % (time.ctime(ts), message)
    out+='<a href="#new">Add a Reminder</a>'

    sendContent(wml(card("reminders", "Reminder list", out)
        + card("new", "New Reminder", getNewForm())))

def doAdd(bp, fs):
    when=fs["when"].value
    msg=fs["msg"].value

    ts=backpack.getRelativeTime(when)
    formattedTs=backpack.formatTime(ts)

    bp.reminder.create(msg, formattedTs)
    sendContent(wml(card("added", "Added Reminder",
        "Added a reminder for %s:  %s" % (time.ctime(ts), msg))))

if __name__ == '__main__':
    doCallback({"list": doList, "add": doAdd})
