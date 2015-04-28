#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys, unittest, collections, copy, re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pycwl import *

class TestPyCWL(unittest.TestCase):
    def setUp(self):
        pass

    def test_basic_pycwl_statements(self):
        h = CloudWatchLogHandler()

        logger = logging.getLogger(__name__)
        #logger.addHandler(CloudWatchLogHandler(threading=True))
        logger.addHandler(CloudWatchLogHandler())
        logger.error("test")

if __name__ == "__main__":
    unittest.main()
