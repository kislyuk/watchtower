#!/usr/bin/env python3
# coding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys, unittest, collections, copy, re

print(sys.version)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from watchtower import *
from eight import *

class TestPyCWL(unittest.TestCase):
    def setUp(self):
        pass

    def test_basic_pycwl_statements(self):
        h = CloudWatchLogHandler()
        loggers = []
        for i in range(5):
            logger = logging.getLogger("logger{}".format(i))
            logger.addHandler(h)
            #logger.addHandler(CloudWatchLogHandler(use_queues=False))
            loggers.append(logger)
        for i in range(10001):
            for logger in loggers:
                logger.error("test")
        import time
        time.sleep(1)
        for i in range(9000):
            for logger in loggers:
                logger.error("test")
        for i in range(1001):
            for logger in loggers:
                logger.error("test")

    def test_flush_safing(self):
        handler = CloudWatchLogHandler()
        logger = logging.getLogger("l")
        logger.addHandler(handler)
        handler.flush()
        logger.critical("msg")

    def test_json_logging(self):
        handler = CloudWatchLogHandler()
        logger = logging.getLogger("json")
        logger.addHandler(handler)
        for i in range(10):
            logger.critical(dict(src="foo", event=str(i), stack=[1, 2, 3, i], details={}))

    def test_multiple_handlers(self):
        # FIXME: multiple active CloudWatchLogHandlers cause daemon thread crashes at exit. This can probably be fixed with thread locals.
        pass

if __name__ == "__main__":
    unittest.main()
