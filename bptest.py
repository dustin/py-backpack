#!/usr/bin/env python
"""
Tests for the backpacks.

Copyright (c) 2005  Dustin Sallings <dustin@spy.net>
"""
# arch-tag: 0BCECE3E-2629-498A-A897-C66F6DC41EB4

import os
import sys
import time
import unittest
import exceptions
import xml.dom.minidom

import backpack

# These tests all assume you're in California.
os.environ['TZ']='US/Pacific'
time.tzset()

class BaseCase(unittest.TestCase):
    """Base case for all test cases."""

    def getFileData(self, p):
        f=open(p)
        r=f.read()
        f.close()
        return r

class UtilTest(unittest.TestCase):
    """Utility function tests."""

    def testRelativeTime(self):
        """Test relative time calculations"""
        # the time at which I started writing this test
        # (9 is today in the future)
        earlyMorning=1121844562.8812749
        # Later in the afternoon
        afterNoon=1121887792.692405
        # Evening
        evening=1121909413.8556659

        # Alias
        relTime=backpack.getRelativeTime

        self.assertEquals(time.ctime(relTime("fifteen", earlyMorning)),
            "Wed Jul 20 00:44:22 2005")
        self.assertEquals(time.ctime(relTime("nexthour", earlyMorning)),
            "Wed Jul 20 01:05:00 2005")
        self.assertEquals(time.ctime(relTime("later", earlyMorning)),
            "Wed Jul 20 02:29:22 2005")
        self.assertEquals(time.ctime(relTime("morning", earlyMorning)),
            "Wed Jul 20 10:00:00 2005")
        self.assertEquals(time.ctime(relTime("afternoon", earlyMorning)),
            "Wed Jul 20 14:00:00 2005")
        self.assertEquals(time.ctime(relTime("evening", earlyMorning)),
            "Wed Jul 20 19:00:00 2005")
        self.assertEquals(time.ctime(relTime("coupledays", earlyMorning)),
            "Fri Jul 22 00:29:22 2005")
        self.assertEquals(time.ctime(relTime("nextweek", earlyMorning)),
            "Wed Jul 27 00:29:22 2005")
        # Later in the day...
        self.assertEquals(time.ctime(relTime("morning", afterNoon)),
            "Thu Jul 21 10:00:00 2005")
        self.assertEquals(time.ctime(relTime("afternoon", afterNoon)),
            "Wed Jul 20 14:00:00 2005")
        # Still yet later
        self.assertEquals(time.ctime(relTime("afternoon", evening)),
            "Thu Jul 21 14:00:00 2005")

    def testRelativeTimeDefault(self):
        """Test a default relative time."""
        # This test is not as predictable, so we can only ensure they're in the
        # future.
        now=time.time()
        for rel in ["later", "morning", "afternoon", "coupledays", "nextweek"]:
            self.failUnless(backpack.getRelativeTime(rel) > now, rel)

    def testTimeParsing(self):
        """Test the time parser"""
        ts=backpack.parseTime("2005-02-02 13:35:35")
        self.assertEquals(time.ctime(ts), "Wed Feb  2 13:35:35 2005")

    def testTimeFormatting(self):
        """Test the time formatter"""
        # When I wrote this test
        then=1121847564.8214879
        s=backpack.formatTime(then)
        self.assertEquals(s, "2005-07-20 01:19:24")

class BackpackAPITest(BaseCase):
    """Test the base backpack functionality."""

    def setUp(self):
        self.bp=backpack.Backpack("x", "y")

    def testConstructors(self):
        """Test the constructors and data work the way I think they do"""
        bp1=backpack.BackpackAPI("x", "y")
        self.failIf(bp1.debug, "first debug is set")

        bp2=backpack.BackpackAPI("x", "y", True)
        self.failUnless(bp2.debug, "second debug is not set")
        self.failIf(bp1.debug, "first debug is set after second")

        bp3=backpack.BackpackAPI("x", "y")
        self.failIf(bp3.debug, "third debug is set")

    def testException(self):
        """Validate exception parsing"""
        try:
            bpapi=backpack.BackpackAPI("x", "y")
            data=bpapi._parseDocument(self.getFileData("data/error404.xml"))
            self.fail("Parsed 404 error into " + data.toprettyxml())
        except backpack.BackpackError, e:
            self.assertEquals(e.code, 404)
            self.assertEquals(e.msg, "Record not found")

class ReminderTest(BaseCase):
    """Test reminder-specific stuff."""

    def testReminderParser(self):
        """Validate reminder parsing."""
        reminder=backpack.ReminderAPI("x", "y")
        data=reminder._parseDocument(self.getFileData("data/reminders.xml"))
        rv=reminder._parseReminders(data)
        expected=[
            (1121755020.0, 52373, 'Get API working.'),
            (1121763600.0, 52372, 'Be asleep.')]
        self.assertEquals(rv, expected)

class PageTest(BaseCase):
    """Test the page code."""

    def testPageListParser(self):
        """Test the page list parser."""
        page=backpack.PageAPI("x", "y")
        data=page._parseDocument(self.getFileData("data/pages.xml"))
        rv=page._parsePageList(data)

    def testPageParser(self):
        """Test the individual page parser."""
        page=backpack.PageAPI("x", "y")
        data=page._parseDocument(self.getFileData("data/page.xml"))
        rv=page._parsePage(data)

        self.assertEquals(rv.title, 'Ajax Summit')
        self.assertEquals(rv.id, 1133)
        self.assertEquals(rv.emailAddress, 'ry87ib@backpackit.com')
        self.assertEquals(rv.notes, 
                [(1019, '', 1116113942.0, u"With O'Reilly and Adaptive Path"),
                 (1020, u'Hotel', 1116114071.0, u"Staying at the Savoy")])
        self.assertEquals(rv.lists, [(937,'Trip to SF')])
        self.assertEquals(rv.tags, [(4, 'Technology'),
            (5, 'Travel')])

    def testSearchResultParser(self):
        """Test the search result parser"""
        page = backpack.PageAPI("x", "y")
        data = page._parseDocument(self.getFileData("data/search.xml"))
        rv = page._parseSearchResult(data)

        self.assertEquals(len(rv), 2)
        self.assertEquals(rv[0].pageId, 1134)
        self.assertEquals(rv[0].pageTitle, "Haystack")
        self.assertEquals(rv[0].type, "note")
        self.assertEquals(rv[0].containerId, 33469)
        self.assertEquals(rv[1].pageId, 2482)
        self.assertEquals(rv[1].pageTitle, "Sewing")
        self.assertEquals(rv[1].type, "list")
        self.assertEquals(rv[1].containerId, 34263)

class ExportTest(BaseCase):
    """Test the backup code."""

    def testExportParser(self):
        """Test the export parser doesn't break."""
        exp=backpack.ExportAPI("x", "y")
        data=exp._parseDocument(self.getFileData("data/export.xml"))
        pages, reminders=exp._parseBackup(data)
        expectedPageIds=[173034, 166626, 201574, 200381, 198053, 202561]
        expectedPageIds.sort()
        gotPageIds=[x[0] for x in pages]
        gotPageIds.sort()
        self.assertEquals(gotPageIds, expectedPageIds)

        expectedReminderIds=[51604, 51613, 52079, 52373, 52403]
        gotReminderIds=[x[1] for x in reminders]
        self.assertEquals(gotReminderIds, expectedReminderIds)


class ListItemTest(BaseCase):
    """Test the list item code"""
    
    def testListItemParser(self):
        """Test the list item parser"""
        li=backpack.ListItemAPI("x", "y")
        data = li._parseDocument(self.getFileData("data/listitem.xml"))
        actual = li._parseListItems(data)
        expected = [(1, False, "Hello world!"), 
                    (2, False, "More world!"),
                    (3, True, "Done world!")]
        self.assertEquals(actual, expected)
        
class ListTest(BaseCase):
    """Test the list code."""

    def testListListParser(self):
        """Test parsing the List list"""
        l=backpack.ListAPI("x", "y")
        data=l._parseDocument(self.getFileData("data/list.xml"))
        gotLists=l._parseLists(data)
        expectedLists = [(1, "greetings"), (2, "goodbyes")]
        self.assertEquals(gotLists, expectedLists)

class NotesTest(BaseCase):
    """Test the notes code."""

    def testNoteListParser(self):
        """Test the notes list parser."""
        n=backpack.NoteAPI("x", "y")
        data=n._parseDocument(self.getFileData("data/notelist.xml"))
        notes=n._parseNotes(data)

        expected=[(263366, 'Test Note', 1124528874.0, 'This is a test note.')]
        self.assertEquals(notes, expected)

class EmailTest(BaseCase):
    """Test the email code."""

    def testAllEmails(self):
        """Test parsing the email list."""
        e=backpack.EmailAPI("x", "y")
        data=e._parseDocument(self.getFileData("data/emaillist.xml"))
        emails=e._parseEmails(data)
        expected=[(17507, 'test backpack email 2', 1124529799.0),
            (17506, 'test backpack email 1', 1124529776.0)]
        nobodies=[x[0:-1] for x in emails]
        self.assertEquals(nobodies, expected)

    def testIndividualEmail(self):
        """Test parsing an individual email."""
        e=backpack.EmailAPI("x", "y")
        data=e._parseDocument(self.getFileData("data/email.xml"))
        email=e._parseEmails(data)[0]
        expected=(17507, 'test backpack email 2', 1124529799.0)
        self.assertEquals(email[0:-1], expected)

class TagTest(BaseCase):
    """Test the tagging code."""

    def testCleaning(self):
        """Test the tag cleaner code."""
        t=backpack.TagAPI("x", "y")
        cleaned=t._cleanTags(["a", "abc", "abc def"])
        expected=["a", "abc", '"abc def"']
        self.assertEquals(cleaned, expected)

    def testBadCleaning(self):
        """Test the tag cleaner with invalid input."""
        t=backpack.TagAPI("x", "y")
        try:
            cleaned=t._cleanTags(["a", '"bc d"'])
            self.fail("Cleaned tags that shouldn't be cleaned:  " + `cleaned`)
        except exceptions.ValueError, e:
            self.assertEquals("Tags can't have quotes.", str(e))

    def testPagesForTagParse(self):
        """Test parsing pages for tag response."""
        t=backpack.TagAPI("x", "y")
        data=t._parseDocument(self.getFileData("data/pagesfortag.xml"))
        results=t._parseTaggedPageList(data)
        expected=[(173034, 'Backpack API'), (18852, 'Nonsense')]
        self.assertEquals(results, expected)

if __name__ == '__main__':
    unittest.main()
