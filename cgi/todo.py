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

def getModifyForm():
    rv="""
Modifying $n ($i)<br/>
<select name="a" title="Action">
    <option value="check">Check</option>
    <option value="delete">Delete</option>
    <option value="mtop">Move to Top</option>
    <option value="mup">Move Up</option>
    <option value="mbottom">Move to Bottom</option>
    <option value="mdown">Move Down</option>
</select><br/>
<anchor title="Modify">
    <go href="/cgi-bin/bp/todo.py?r=%(rnd)d" method="post">
        <postfield name="i" value="$(i)"/>
        <postfield name="a" value="$(a)"/>
        <postfield name="action" value="modify"/>
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
        + card("m", "Modify Todo", getModifyForm())))

def doAdd(bp, fs):
    what=fs["w"].value

    id, complete, text=bp.list.create(getTodoId(), what)
    sendContent(wml(card("added", "Added Todo",
        "Added a todo item with ID %d:  %s" % (id, text))))

def modify(bp, fs):
    id=int(fs["i"].value)
    action=fs["a"].value

    actions={
        "check": (bp.list.toggle,
            "Toggled", "Your todo entry has been marked done."),
        "delete": (bp.list.destroy,
            "Deleted", "Your todo entry has been deleted."),
        'mtop': (lambda a, b: bp.list.move(a, b, backpack.ListAPI.MOVE_TO_TOP),
            "Moved", "Your todo entry has been moved to the top."),
        'mup': (lambda a, b: bp.list.move(a, b, backpack.ListAPI.MOVE_HIGHER),
            "Moved", "Your todo entry has been moved up."),
        'mbottom': (lambda a, b:
                bp.list.move(a, b, backpack.ListAPI.MOVE_TO_BOTTOM),
            "Moved", "Your todo entry has moved to the bottom."),
        'mdown': (lambda a, b: bp.list.move(a, b, backpack.ListAPI.MOVE_LOWER),
            "Moved", "Your todo entry has moved lower."),
    }

    actions[action][0](getTodoId(), id)
    sendContent(wml(card("modified", actions[action][1], actions[action][2])))

if __name__ == '__main__':
    doCallback({"list": doList, "add": doAdd, "modify": modify})
