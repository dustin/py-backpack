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
What: <input type="text" name="w"/><br/>

<anchor title="Add">
    <go href="/cgi-bin/bp/todo.py?r=%(rnd)d" method="post">
        <postfield name="w" value="$(w)"/>
        <postfield name="action" value="add"/>
    </go>
</anchor>
""" % {'rnd': random.Random().randint(0,10000)}
    return rv

def getDoneForm():
    rv="""
Completing $n ($i)<br/>
<anchor title="Complete">
    <go href="/cgi-bin/bp/todo.py?r=%(rnd)d" method="post">
        <postfield name="i" value="$(i)"/>
        <postfield name="action" value="markDone"/>
    </go>
</anchor>
""" % {'rnd': random.Random().randint(0,10000)}
    return rv

def getTodoId():
    return int(conf.get('backpack', 'todopage'))

def doList(bp, fs):
    # Get all of the todo entries that are not complete
    todo=[x for x in bp.list.list(getTodoId()) if not x[1]]
    out="Found %d todos:<br/>" % (len(todo))
    for id, complete, text in todo:
        out += '\n* <anchor>%s<go href="#m">\n' \
            '  <setvar name="i" value="%d"/>\n' \
            '  <setvar name="n" value="%s"/></go></anchor><br/>\n' \
            % (text, id, text)
    out+='<br/><a href="#new">Add a todo</a>'

    sendContent(wml(card("todo", "Todo list", out)
        + card("new", "New Todo", getNewForm())
        + card("m", "Mark Done", getDoneForm())))

def doAdd(bp, fs):
    what=fs["w"].value

    id, complete, text=bp.list.create(getTodoId(), what)
    sendContent(wml(card("added", "Added Todo",
        "Added a todo item with ID %d:  %s" % (id, text))))

def markDone(bp, fs):
    id=int(fs["i"].value)

    bp.list.toggle(getTodoId(), id)
    sendContent(wml(card("toggled", "Completed",
        "Your todo entry has been marked done.")))


if __name__ == '__main__':
    doCallback({"list": doList, "add": doAdd, "markDone": markDone})
