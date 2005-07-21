#!/usr/bin/env python
"""
Tests for the backpacks.

Copyright (c) 2005  Dustin Sallings <dustin@spy.net>
"""
# arch-tag: 0BCECE3E-2629-498A-A897-C66F6DC41EB4

import sys
import time
import unittest
import xml.dom.minidom

import backpack

class BPTest(unittest.TestCase):

    def setUp(self):
        self.bp=backpack.Backpack("x", "y")

    def getFileData(self, p):
        f=open(p)
        r=f.read()
        f.close()
        return r

    def testConstructors(self):
        """Test the constructors and data work the way I think they do"""
        bp1=backpack.BackpackAPI("x", "y")
        self.failIf(bp1.debug, "first debug is set")

        bp2=backpack.BackpackAPI("x", "y", True)
        self.failUnless(bp2.debug, "second debug is not set")
        self.failIf(bp1.debug, "first debug is set after second")

        bp3=backpack.BackpackAPI("x", "y")
        self.failIf(bp3.debug, "third debug is set")

    def testReminderParser(self):
        """Validate reminder parsing."""
        reminder=backpack.Reminder("x", "y")
        data=reminder._parseDocument(self.getFileData("data/reminders.xml"))
        rv=reminder._parseReminders(data)
        expected=[
            (1121755020.0, 52373, 'Get API working.'),
            (1121763600.0, 52372, 'Be asleep.')]
        self.assertEquals(rv, expected)

    def testException(self):
        """Validate exception parsing"""
        try:
            bpapi=backpack.BackpackAPI("x", "y")
            data=bpapi._parseDocument(self.getFileData("data/error404.xml"))
            self.fail("Parsed 404 error into " + data.toprettyxml())
        except backpack.BackpackError, e:
            self.assertEquals(e.code, 404)
            self.assertEquals(e.msg, "You failed")

    def testTimeParsing(self):
        """Test the time parser"""
        bpapi=backpack.BackpackAPI("x", "y")
        ts=bpapi._parseTime("2005-02-02 13:35:35")
        self.assertEquals(time.ctime(ts), "Wed Feb  2 13:35:35 2005")

    def testTimeFormatting(self):
        """Test the time formatter"""
        # When I wrote this test
        then=1121847564.8214879
        bpapi=backpack.BackpackAPI("x", "y")
        s=bpapi.formatTime(then)
        self.assertEquals(s, "2005-07-20 01:19:24")

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
        relTime=self.bp.reminder.getRelativeTime

        self.assertEquals(time.ctime(relTime("fifteen", earlyMorning)),
            "Wed Jul 20 00:44:22 2005")
        self.assertEquals(time.ctime(relTime("nexthour", earlyMorning)),
            "Wed Jul 20 01:05:00 2005")
        self.assertEquals(time.ctime(relTime("later", earlyMorning)),
            "Wed Jul 20 02:29:22 2005")
        self.assertEquals(time.ctime(relTime("morning", earlyMorning)),
            "Wed Jul 20 09:00:00 2005")
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
            "Thu Jul 21 09:00:00 2005")
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
            self.failUnless(self.bp.reminder.getRelativeTime(rel) > now, rel)

if __name__ == '__main__':
    unittest.main()
