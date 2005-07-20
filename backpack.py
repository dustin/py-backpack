#!/usr/bin/env python
"""
Backpack API

Copyright (c) 2005  Dustin Sallings <dustin@spy.net>
"""
# arch-tag: 213B96AE-E458-416C-94E3-5A486CD6DE80

import os
import sys
import time
import urllib2
import datetime
import exceptions
import xml.dom.minidom

try:
    False
except NameError:
    True=1
    False=0

class BackpackError(exceptions.Exception):

    def __init__(self, code, msg):
        self.code=code;
        self.msg=msg

    def __repr__(self):
        return "<code=%d, msg=%s>" % (self.code, self.msg)

class Backpack(object):
    """Interface to the backpack API"""

    TIMEFMT="%Y-%m-%d %H:%M:%S"

    def __init__(self, u, k, debug=False):
        """Get a Backpack object to the given URL and key"""
        if u[-1] == '/':
            u=u[:-1]
        self.url=u
        self.key=k

        self.debug=debug

    # Parse a backpack document, throwing a BackpackError if the document
    # indicates an exception
    def _parseDocument(self, docString):
        document=xml.dom.minidom.parseString(docString)
        # Check for error
        responseEl=document.getElementsByTagName("response")[0]
        if responseEl.getAttribute("success") != "true":
            er=responseEl.getElementsByTagName("error")[0]
            raise BackpackError(int(er.getAttribute("code")),
                str(er.firstChild.data))
        return document

    def __call(self, path, data=""):
        p={'token':self.key, 'extra':data}
        reqData="""<request><token>%(token)s</token>%(extra)s</request>""" % p
        theUrl=self.url + path

        if self.debug:
            print ">>(%s)\n%s" % (theUrl, reqData)

        req=urllib2.Request(theUrl, reqData, {'X-POST_DATA_FORMAT': 'xml'})
        opener=urllib2.build_opener()

        o=opener.open(req)
        result=o.read()
        o.close()

        if self.debug:
            print "<< %s" % (result,)

        return self._parseDocument(result)

    # Parse a timestamp
    def _parseTime(self, timeString):
        return(time.mktime(time.strptime(timeString, self.TIMEFMT)))

    def getRelativeTime(self, rel, t=None):
        """Get the time relative to the specified time (default to now).

           Allowed relative terms:
           * later
           * morning
           * afternoon
           * coupledays
           * nextweek"""

        if t is None:
            t=time.time()

        now=datetime.datetime.fromtimestamp(t)
        rv=t

        if rel == 'later':
            # Two hours later
            rv += 7200
        elif rel == 'morning':
            then=datetime.datetime(now.year, now.month, now.day, 9, 0, 0)
            rv=time.mktime(then.timetuple())
        elif rel == 'afternoon':
            then=datetime.datetime(now.year, now.month, now.day, 14, 0, 0)
            rv=time.mktime(then.timetuple())
        elif rel == 'coupledays':
            rv=t + (86400 * 2)
        elif rel == 'nextweek':
            rv=t + (86400 * 7)
        else:
            raise ValueError("Unknown rel type:  " + rel)

        # Make sure the time is in the relative future
        while rv < t:
            rv += 86400

        return rv

    def formatTime(self, t):
        """Format a timestamp for an API call"""
        return(time.strftime(self.TIMEFMT, time.localtime(t)))

    # parse the reminders xml
    def _parseReminders(self, document):

        rv=[]

        reminders=document.getElementsByTagName("reminder")
        for r in reminders:
            timestamp=self._parseTime(r.getAttribute("remind_at"))
            id=int(r.getAttribute("id"))
            message=str(r.firstChild.data)

            rv.append((timestamp, id, message))

        return rv

    def getUpcomingReminders(self):
        """Get a list of upcoming reminders.

           Returns a list of (timestamp, id, message)"""
        x=self.__call("/ws/reminders")

        return self._parseReminders(x)

    def createReminder(self, content, at=None):
        """Create a reminder with the given content.

           If a time is not given, the content is expected to start with the
           +minute or +hour:minute format as specified by backpack."""

        val=""
        if at is None:
            if content[0] != '+':
                raise ValueError("No at, and content not beginning with +")
            val="""<content>%s</content>""" % (content,)
        else:
            val="<content>%s</content><remind_at>%s</remind_at>" \
                % (content, at)

        x=self.__call("/ws/reminders/create",
            "<reminder>%s</reminder>" % (val,))
        return self._parseReminders(x)

    def updateReminder(self, id, content, at=None):
        """Update the given reminder.

           If a time is not given, only the content will be updated."""

        val=""
        if at is None:
            val="""<content>%s</content>""" % (content,)
        else:
            val="<content>%s</content><remind_at>%s</remind_at>" \
                % (content, at)

        x=self.__call("/ws/reminders/update/%d" % (id, ),
            "<reminder>%s</reminder>" % (val, ))
        return self._parseReminders(x)

    def deleteReminder(self, id):
        """Delete a reminder"""
        x=self.__call("/ws/reminders/destroy/%d" % (id,))
