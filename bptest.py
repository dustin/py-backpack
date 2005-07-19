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

    def testReminderParser(self):
        """Validate reminder parsing."""
        data=self.bp._parseDocument(self.getFileData("data/reminders.xml"))
        rv=self.bp._parseReminders(data)
        expected=[
            (1121755020.0, 52373, 'Get API working.'),
            (1121763600.0, 52372, 'Be asleep.')]
        self.assertEquals(rv, expected)

    def testException(self):
        """Validate exception parsing"""
        try:
            data=self.bp._parseDocument(self.getFileData("data/error404.xml"))
            self.fail("Parsed 404 error into " + data.toprettyxml())
        except backpack.BackpackError, e:
            self.assertEquals(e.code, 404)
            self.assertEquals(e.msg, "You failed")

    def testTimeParsing(self):
        """Test the time parser"""
        ts=self.bp._parseTime("2005-02-02 13:35:35")
        self.assertEquals(time.ctime(ts), "Wed Feb  2 13:35:35 2005")

if __name__ == '__main__':
    unittest.main()
