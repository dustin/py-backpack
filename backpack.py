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

class BackpackAPI(object):
    """Interface to the backpack API"""

    TIMEFMT="%Y-%m-%d %H:%M:%S"
    debug=False
    url=None
    key=None

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

    # Perform the actual call
    def _call(self, path, data=""):
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

            * fifteen - fifteen minutes from now
            * nexthour - five minutes after the beginning of the next hour
            * later - two hours from now
            * morning - 10:00
            * afternoon - 14:00
            * evening - 19:00
            * coupledays - two days from now
            * nextweek - seven days from now
        """

        if t is None:
            t=time.time()

        now=datetime.datetime.fromtimestamp(t)
        rv=t

        if rel == 'fifteen':
            # Fifteen minutes later
            rv += (15 * 60)
        elif rel == 'later':
            # Two hours later
            rv += 7200
        elif rel == 'nexthour':
            # Top of next hour
            # Increment by an hour
            rv += 3600
            # Increment an hour
            then=datetime.datetime.fromtimestamp(rv)
            # Then set the hour and minute
            then=datetime.datetime(then.year, then.month, then.day, then.hour,
                5, 0)
            rv=time.mktime(then.timetuple())
        elif rel == 'morning':
            then=datetime.datetime(now.year, now.month, now.day, 10, 0, 0)
            rv=time.mktime(then.timetuple())
        elif rel == 'afternoon':
            then=datetime.datetime(now.year, now.month, now.day, 14, 0, 0)
            rv=time.mktime(then.timetuple())
        elif rel == 'evening':
            then=datetime.datetime(now.year, now.month, now.day, 19, 0, 0)
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

class ReminderAPI(BackpackAPI):
    """Backpack reminder API."""

    def __init__(self, u, k, debug=False):
        """Get a Reminder object to the given URL and key"""
        BackpackAPI.__init__(self, u, k, debug)

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

    def list(self):
        """Get a list of upcoming reminders.

           Returns a list of (timestamp, id, message)"""
        x=self._call("/ws/reminders")

        return self._parseReminders(x)

    def create(self, content, at=None):
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

        x=self._call("/ws/reminders/create",
            "<reminder>%s</reminder>" % (val,))
        return self._parseReminders(x)

    def update(self, id, content, at=None):
        """Update the given reminder.

           If a time is not given, only the content will be updated."""

        val=""
        if at is None:
            val="""<content>%s</content>""" % (content,)
        else:
            val="<content>%s</content><remind_at>%s</remind_at>" \
                % (content, at)

        x=self._call("/ws/reminders/update/%d" % (id, ),
            "<reminder>%s</reminder>" % (val, ))
        return self._parseReminders(x)

    def delete(self, id):
        """Delete a reminder"""
        x=self._call("/ws/reminders/destroy/%d" % (id,))

class Page(object):
    """An individual page.

    * Notes are in the form of (id, title, createdDate, msg).
    * Complete and incomplete items are in the form of (id, text)
    * Links are in the form of (id, title)
    * Tags are in the form of (id, name)

    """

    title=None
    id=None
    emailAddress=None
    body=None
    notes=[]
    completeItems=[]
    incompleteItems=[]
    links=[]
    tags=[]

class PageAPI(BackpackAPI):
    """Backpack page API."""

    def __init__(self, u, k, debug=False):
        """Get a Page object to the given URL and key"""
        BackpackAPI.__init__(self, u, k, debug)

    # parse the page list xml
    def _parsePageList(self, document):
        rv=[]
        reminders=document.getElementsByTagName("page")
        for r in reminders:
            id=int(r.getAttribute("id"))
            scope=str(r.getAttribute("scope"))
            title=str(r.getAttribute("title"))

            rv.append((id, scope, title))

        return rv

    # get an iterator on the named node of the zeroth node of the given list
    def __linkIter(self, node, container, elementname):
        rv=[]
        nlist=node.getElementsByTagName(container)
        if len(nlist) > 0:
            rv=nlist[0].getElementsByTagName(elementname)
        return rv

    # Parse the individual page xml
    def _parsePage(self, document):
        rv=Page()
        page=document.getElementsByTagName("page")[0]

        rv.title=page.getAttribute("title")
        rv.id=int(page.getAttribute("id"))
        rv.emailAddress=page.getAttribute("email_address")

        desc=page.getElementsByTagName("description")[0]
        rv.body=str(desc.firstChild.data).strip()

        for note in self.__linkIter(page, "notes", "note"):
            rv.notes.append( (int(note.getAttribute("id")),
                str(note.getAttribute("title")),
                self._parseTime(note.getAttribute("created_at")),
                str(note.firstChild.data).strip()))

        # Parse a task list into a destination list
        def parseItems(n, which, destList):
            for item in self.__linkIter(n, which, "item"):
                destList.append( (int(item.getAttribute("id")),
                    str(item.firstChild.data).strip()))

        items=page.getElementsByTagName("items")
        if len(items) > 0:
            parseItems(items[0], "incomplete", rv.incompleteItems)
            parseItems(items[0], "completed", rv.completeItems)

        for link in self.__linkIter(page, "linked_pages", "page"):
            rv.links.append( (int(link.getAttribute("id")),
                str(link.getAttribute("title"))))

        for tag in self.__linkIter(page, "tags", "tag"):
            rv.tags.append( (int(tag.getAttribute("id")),
                str(tag.getAttribute("name"))))

        return rv

    def list(self):
        """List all pages
        
           Returns a list of (id, scope, title) tuples.
        """
        x=self._call("/ws/pages/all")

        return self._parsePageList(x)

    def get(self, id):
        """Get a given page by id.
        
           Returns a Page instance.
        """
        x=self._call("/ws/page/%d" % (id,))

        return self._parsePage(x)

    def create(self, title, description):
        """Create a new page.

           Returns (id, title)"""

        data="<page><title>%s</title><description>%s</description></page>" \
            % (title, description)
        x=self._call("/ws/pages/new", data)

        p=x.getElementsByTagName("page")[0]
        return (int(p.getAttribute("id")), str(p.getAttribute("title")))

    def delete(self, id):
        """Delete a page"""
        x=self._call("/ws/page/%d/destroy" % (id,))

    def updateTitle(self, id, title):
        """Update a title"""
        data="<page><title>%s</title></page>" % (title,)
        x=self._call("/ws/page/%d/update_title" % (id,), data)

    def updateDescription(self, id, desc):
        """Update a description"""
        data="<page><description>%s</description></page>" % (desc,)
        x=self._call("/ws/page/%d/update_body" % (id,), data)

    def duplicate(self, id):
        """Duplicate a page, get the new (id, title)"""
        x=self._call("/ws/page/%d/duplicate" % (id,))

        p=x.getElementsByTagName("page")[0]
        return (int(p.getAttribute("id")), str(p.getAttribute("title")))

    def linkTo(self, id, linkId):
        """Link a page to another page."""
        data="<linked_page_id>%d</linked_page_id>" % (linkId,)
        x=self._call("/ws/page/%d/link" % (id,), data)

    def unlink(self, id, linkId):
        """Unlink a page from another page."""
        data="<linked_page_id>%d</linked_page_id>" % (linkId,)
        x=self._call("/ws/page/%d/unlink" % (id,), data)

    def share(self, id, emailAddresses=[], isPublic=False):
        """Share this page with others."""
        data=""
        if len(emailAddresses) > 0:
            data+="<email_addresses>%s</email_addresses>" \
                % (' '.join(emailAddresses),)
        data+="<page><public>%d</public></page>" % (isPublic,)
        x=self._call("/ws/page/%d/share" % (id,), data)

    def unshare(self, id):
        """Unshare a page."""
        x=self._call("/ws/page/%d/unshare_friend_page" % (id,))

    def email(self, id):
        """Email yourself a page."""
        x=self._call("/ws/page/%d/email" % (id,))

class Backpack(object):
    """Interface to all of the backpack APIs.

       * page - PageAPI object
       * reminder - ReminderAPI object
    
    """

    reminder=None
    page=None

    def __init__(self, url, key, debug=False):
        """Initialize the backpack APIs."""
        self.reminder=ReminderAPI(url, key, debug)
        self.page=PageAPI(url, key, debug)
