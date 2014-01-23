#!/usr/bin/env python
"""
Interface to the Backpack API as specified at the following location:

    http://developer.37signals.com/backpack/

Example:

    # Get a specific Page instance.
    bp=backpack.Backpack("http://yourusername.backpackit.com/",
        "yourApiKeyAsSeenOnYourAccountPage")
    thePage=bp.page.get(23852)

    # Schedule a reminder for two hours from now
    bp.reminder.create("Do this",
        backpack.formatTime(backpack.getRelativeTime("later")))
"""

# Copyright (c) 2005  Dustin Sallings <dustin@spy.net>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# <http://www.opensource.org/licenses/mit-license.php>

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

TIMEFMT="%Y-%m-%d %H:%M:%S"

def parseTime(timeString):
    """Parse a timestamp from a backpack response."""
    return(time.mktime(time.strptime(timeString, TIMEFMT)))

def formatTime(t):
    """Format a timestamp for an API call"""
    return(time.strftime(TIMEFMT, time.localtime(t)))

def getRelativeTime(rel, t=None):
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


class BackpackError(exceptions.Exception):
    """Root exception thrown when a backpack error occurs."""

    def __init__(self, code, msg):
        exceptions.Exception.__init__(self, msg)
        self.code=code;
        self.msg=msg

    def __repr__(self):
        return "<code=%d, msg=%s>" % (self.code, self.msg)

class PageLimitExceeded(BackpackError):
    """Exception thrown when an attempt to create a page fails with a 403."""

    def __init__(self, msg):
        BackpackError.__init__(self, 403, msg)

class BackpackAPI(object):
    """Interface to the backpack API"""

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

    def _parseListItems(self, document):
        """Parses list items from from a minidom document

        Returns a list of (id, completed boolean, item text)
        """
        rv=[]
        for item in document.getElementsByTagName("item"):
            rv.append((int(item.getAttribute("id")),
                item.getAttribute("completed") == "true",
                unicode(item.firstChild.data)))
        return rv

    def _parseLists(self, document):
        rv=[]
        for list in document.getElementsByTagName("list"):
            rv.append( (int(list.getAttribute("id")),
                unicode(list.getAttribute("name"))) )
        return rv

    def _parseNotes(self, document):
        rv=[]
        for note in document.getElementsByTagName("note"):
            try:
                childData = unicode(note.firstChild.data).strip()
            except AttributeError:
                childData = ''
            rv.append( (int(note.getAttribute("id")),
                unicode(note.getAttribute("title")),
                parseTime(note.getAttribute("created_at")),
                childData))
        return rv

    # Parse a backpack document, throwing a BackpackError if the document
    # indicates an exception
    def _parseDocument(self, docString):
        document=xml.dom.minidom.parseString(docString)
        # Check for error
        responseEl=document.getElementsByTagName("response")[0]
        if responseEl.getAttribute("success") != "true":
            er=responseEl.getElementsByTagName("error")[0]
            raise BackpackError(int(er.getAttribute("code")),
                unicode(er.firstChild.data))
        return document

    # Perform the actual call
    def _call(self, path, data=""):
        p={'token':self.key, 'extra':data}
        reqData="""<request><token>%(token)s</token>%(extra)s</request>""" % p
        theUrl=self.url + path

        if self.debug:
            print ">>(%s)\n%s" % (theUrl, reqData)

        req=urllib2.Request(theUrl, reqData, {'Content-Type': 'application/xml'})
        opener=urllib2.build_opener()

        o=opener.open(req)
        result=o.read()
        o.close()

        if self.debug:
            print "<< %s" % (result,)

        return self._parseDocument(result)

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
            timestamp=parseTime(r.getAttribute("remind_at"))
            id=int(r.getAttribute("id"))
            message=unicode(r.firstChild.data)

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

    def destroy(self, id):
        """Delete a reminder"""
        x=self._call("/ws/reminders/destroy/%d" % (id,))

class Page(object):
    """An individual page.

    * Notes are in the form of (id, title, createdDate, msg).
    * Links are in the form of (id, title)
    * Tags are in the form of (id, name)

    """

    title=None
    id=None
    emailAddress=None
    notes=[]
    lists=[]
    tags=[]

class SearchResult(object):
    """An individual search result.  The object supports the ability to
    retrieve its full representation based on the type of result.  Retrieving
    a writeboard only returns the id at this point, because no Writeboard
    API is currently supported"""

    bp=None         # Backpack instance to enable get
    pageId=None
    pageTitle=None
    type=None
    containerId=None

    def get(self):
        """Returns the appropriate representation of itself based type
        
        list:       Returns the result of Backpack.list.get
        note:       Returns the result of Backpack.notes.list
        writeboard: Returns (page id, page title, writeboard id)
        email:      Returns the result of Backpack.email.get
        """
        if self.type == 'list':
            return self.bp.list.get(self.pageId, self.containerId)
        elif self.type == 'note':
            return self.bp.notes.list(self.pageId)
        elif self.type == 'writeboard_link':
            return (self.pageId, self.pageTitle, self.containerId)
        elif self.type == 'email':
            return self.bp.email.get(self.pageId, self.containerId)


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
            scope=unicode(r.getAttribute("scope"))
            title=unicode(r.getAttribute("title"))

            rv.append((id, scope, title))

        return rv

    def _parseSearchResult(self, document):
        rv = []
        pages = document.getElementsByTagName("page")
        for p in pages:
            for send in p.getElementsByTagName("send"):
                sr = SearchResult()
                sr.bp = Backpack(self.url, self.key, self.debug)
                sr.pageId = int(p.getAttribute("id"))
                sr.pageTitle = unicode(p.getAttribute("title"))
                sr.type = send.firstChild.data
                sr.containerId = int(send.getAttribute("id"))
                rv.append(sr)
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
        rv.notes=self._parseNotes(page)
        rv.lists=self._parseLists(page)

        for tag in self.__linkIter(page, "tags", "tag"):
            rv.tags.append( (int(tag.getAttribute("id")),
                unicode(tag.getAttribute("name"))))

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

    def create(self, title):
        """Create a new page.

           Returns (id, title)"""

        data="<page><title>%s</title></page>" \
            % (title,)
        try:
            x=self._call("/ws/pages/new", data)
        except urllib2.HTTPError, e:
            # A 403 occurs when a page already exists.
            if e.code == 403:
                raise PageLimitExceeded(title)
            else:
                raise e

        p=x.getElementsByTagName("page")[0]
        return (int(p.getAttribute("id")), unicode(p.getAttribute("title")))

    def destroy(self, id):
        """Delete a page"""
        x=self._call("/ws/page/%d/destroy" % (id,))

    def search(self, term):
        """Search for pages containing the term
        
        Returns a list of SearchResult objects.
        """
        data="<term>%s</term>" % term
        x = self._call("/ws/pages/search", data)
        return self._parseSearchResult(x)

    def updateTitle(self, id, title):
        """Update a title"""
        data="<page><title>%s</title></page>" % (title,)
        x=self._call("/ws/page/%d/update_title" % (id,), data)

    def duplicate(self, id):
        """Duplicate a page, get the new (id, title)"""
        x=self._call("/ws/page/%d/duplicate" % (id,))

        p=x.getElementsByTagName("page")[0]
        return (int(p.getAttribute("id")), unicode(p.getAttribute("title")))

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

class ExportAPI(PageAPI, ReminderAPI):
    """Export page API."""

    def __init__(self, u, k, debug=False):
        """Get an Export object to the given URL and key"""
        BackpackAPI.__init__(self, u, k, debug)

    def _parseDocument(self, docString):
        document=xml.dom.minidom.parseString(docString)
        responseEl=document.getElementsByTagName("backpack")[0]
        return document

    def _parseBackup(self, x):
        return self._parsePageList(x), self._parseReminders(x)

    def export(self):
        """Get export of all data from BackPack

        returns (pages, reminders)
        """
        x=self._call("/ws/account/export")

        return(self._parseBackup(x))


class ListAPI(BackpackAPI):
    """Backpack list API."""

    def __init__(self, u, k, debug=False):
        """Get a ListAPI object to the given URL and key"""
        BackpackAPI.__init__(self, u, k, debug)

    def create(self, pageId, name):
        """Creates a new list on the given page

        Returns (id, name)
        """
        data = "<name>%s</name>" % name
        x = self._call("/ws/page/%d/lists/add" % pageId, data)
        l = x.getElementsByTagName("list")[0]
        return ( int(l.getAttribute("id")), unicode(l.getAttribute("name")) )

    def update(self, pageId, listId, name):
        """Changes a list's name"""
        data = "<list><name>%s</name></list>" % name
        self._call("/ws/page/%d/lists/update/%d" % (pageId, listId), data)

    def destroy(self, pageId, listId):
        self._call("/ws/page/%d/lists/destroy/%d" % (pageId, listId))

    def list(self, pageId):
        """Get a list of lists on the given page
        
        list of (id, name)
        """
        x = self._call("/ws/page/%d/lists/list" % pageId)
        return self._parseLists(x)
    
class ListItemAPI(BackpackAPI):
    """Backpack list API."""

    MOVE_LOWER='move_lower'

    MOVE_HIGHER='move_higher'

    MOVE_TO_TOP='move_to_top'

    MOVE_TO_BOTTOM='move_to_bottom'

    def __init__(self, u, k, debug=False):
        """Get a ListAPI object to the given URL and key"""
        BackpackAPI.__init__(self, u, k, debug)

    def list(self, pageId, listId):
        """Get a list of the items on the given list.

        list of (id, completedBoolean, text)
        """
        x=self._call("/ws/page/%d/lists/%d/items/list" % (pageId, listId))
        return self._parseListItems(x)

    def create(self, pageId, listId, text):
        """Create a new entry.
        Return (id, completedBoolean, text)"""
        data="<item><content>%s</content></item>" % (text,)
        x=self._call("/ws/page/%d/lists/%d/items/add" % (pageId, listId), data)
        return self._parseListItems(x)[0]

    def update(self, pageId, listId, id, text):
        """Update an entry."""
        data="<item><content>%s</content></item>" % (text,)
        x=self._call("/ws/page/%d/lists/%d/items/update/%d" % 
                     (pageId, listId, id), data)

    def toggle(self, pageId, listId, id):
        """Toggle an entry."""
        x=self._call("/ws/page/%d/lists/%d/items/toggle/%d" % 
                     (pageId, listId, id))

    def destroy(self, pageId, listId, id):
        """Destroy an entry."""
        x=self._call("/ws/page/%d/lists/%d/items/destroy/%d" % 
                (pageId, listId, id))

    def move(self, pageId, listId, id, direction):
        """Move an entry.
        
        direction can be 'move_lower', 'move_higher', 
                         'move_to_top', and 'move_to_bottom'
        """
        data="<direction>%s</direction>" % (direction,)
        x=self._call("/ws/page/%d/lists/%d/items/move/%d" % 
                (pageId, listId, id), data)

class NoteAPI(BackpackAPI):
    """API to Backpack Notes for a page."""

    def __init__(self, u, k, debug=False):
        """Get a NoteAPI object to the given URL and key"""
        BackpackAPI.__init__(self, u, k, debug)

    def list(self, pageId):
        """Get a list of the items on the given page.

        list of (id, title, timestamp, text)
        """
        x=self._call("/ws/page/%d/notes/list" % pageId)
        return self._parseNotes(x)

    def create(self, pageId, title, body):
        """Create a new entry.
        Return (id, title, timestamp, text)"""
        data="<note><title>%s</title><body>%s</body></note>" % (title, body)
        x=self._call("/ws/page/%d/notes/create" % (pageId,), data)
        return self._parseNotes(x)[0]

    def update(self, pageId, noteId, title, body):
        """Update a note."""
        data="<note><title>%s</title><body>%s</body></note>" % (title, body)
        x=self._call("/ws/page/%d/notes/update/%d" % (pageId, noteId), data)

    def destroy(self, pageId, noteId):
        """Delete a note."""
        x=self._call("/ws/page/%d/notes/destroy/%d" % (pageId, noteId))

class EmailAPI(BackpackAPI):
    """The backpack Email API"""

    def __init__(self, u, k, debug=False):
        """Get a ListAPI object to the given URL and key"""
        BackpackAPI.__init__(self, u, k, debug)

    def _parseEmails(self, x):
        rv=[]
        for item in x.getElementsByTagName("email"):
            rv.append((int(item.getAttribute("id")),
                unicode(item.getAttribute("subject")),
                parseTime(item.getAttribute("created_at")),
                item.firstChild.data))
        return rv

    def list(self, pageId):
        """Get a list of the email on the given page.

        list of (id, subject, timestamp, text)
        """
        x=self._call("/ws/page/%d/emails/list" % pageId)
        return self._parseEmails(x)

    def get(self, pageId, mailId):
        """Get an individual email from the given page.

        (id, subject, timestamp, text)
        """
        x=self._call("/ws/page/%d/emails/show/%d" % (pageId, mailId))
        return self._parseEmails(x)[0]

    def destroy(self, pageId, mailId):
        """Delete an email."""
        x=self._call("/ws/page/%d/emails/destroy/%d" % (pageId, mailId))

class TagAPI(BackpackAPI):
    """The Backpack Tags API."""

    def __init__(self, u, k, debug=False):
        """Get a TagAPI object to the given URL and key"""
        BackpackAPI.__init__(self, u, k, debug)

    def _parseTaggedPageList(self, x):
        rv=[]
        for item in x.getElementsByTagName("page"):
            rv.append((int(item.getAttribute("id")),
                unicode(item.getAttribute("title"))))
        return rv

    def pagesForTag(self, tagId):
        """Get a list of the pages with a given tag ID.
        
        return a list of (id, title)
        """
        x=self._call("/ws/tags/select/%d" % tagId)
        return self._parseTaggedPageList(x)

    def _cleanTags(self, tags):
        """Clean the given tags for API invocation."""
        cleanedTags=[]
        for t in tags:
            if t.find('"') != -1:
                raise exceptions.ValueError("Tags can't have quotes.")
            if t.find(' ') != -1:
                cleanedTags.append('"%s"' % t)
            else:
                cleanedTags.append(t)
        return cleanedTags

    def tagPage(self, pageId, tags):
        """Tag a page with a list of words."""
        data="<tags>%s</tags>" % ' '.join(self._cleanTags(tags))
        x=self._call("/ws/page/%d/tags/tag" % pageId, data)

class Backpack(object):
    """Interface to all of the backpack APIs.

       * page - PageAPI object
       * reminder - ReminderAPI object
       * list - ListAPI object
       * notes - NoteAPI object
       * tags - TagAPI object
       * email - EmailAPI object
       * export - ExportAPI object
    """

    reminder=None
    page=None
    list=None
    notes=None
    email=None
    tags=None
    export=None

    def __init__(self, url, key, debug=False):
        """Initialize the backpack APIs."""
        self.reminder=ReminderAPI(url, key, debug)
        self.page=PageAPI(url, key, debug)
        self.list=ListAPI(url, key, debug)
        self.listItem=ListItemAPI(url, key, debug)
        self.notes=NoteAPI(url, key, debug)
        self.email=EmailAPI(url, key, debug)
        self.tags=TagAPI(url, key, debug)
        self.export=ExportAPI(url, key, debug)
