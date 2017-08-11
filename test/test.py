#!/usr/bin/env python3
# coding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

import collections
import copy
import mock
import logging
import logging.config
import os
import os.path
import re
import sys
import tempfile
import unittest

import boto3
import botocore.configloader
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  # noqa
from watchtower import CloudWatchLogHandler

class TestPyCWL(unittest.TestCase):
    def setUp(self):
        self.test_path = os.path.dirname(__file__)
        self.log_config_yaml_basic = '{0}/logging.yml'.format(self.test_path)
        self.log_config_yaml_profile = '{0}/logging_profile.yml'.format(self.test_path)

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
        handler.close()
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

    def test_logconfig_dictconfig_basic(self):
        with open(self.log_config_yaml_basic, 'r') as yaml_input:
            config_yml = yaml_input.read()
            config_dict = yaml.load(config_yml)
            logging.config.dictConfig(config_dict)
            logger = logging.getLogger('root')
            for i in range(10):
                logger.critical(dict(src="foo2", event=str(i), stack=[1, 2, 3, i], details={}))

    def test_logconfig_dictconfig_profile(self):
        # NOTE: The below is a bit of a hack to get around how Travis CI works so that it
        #   can be fully tested remotely too.

        # save the known configuration values from the ENV vars to a configuration file
        aws_config = tempfile.NamedTemporaryFile()
        with open(aws_config.name, 'w') as boto3_config_file:
            boto3_config_file.write('[profile watchtowerlogger]\n')
            boto3_config_file.write(
                'aws_access_key_id={0}\n'.format(
                    boto3.Session().get_credentials().access_key
                )
            )
            boto3_config_file.write(
                'aws_secret_access_key={0}\n'.format(
                    boto3.Session().get_credentials().secret_key
                )
            )
            boto3_config_file.write(
                'region={0}\n'.format(
                    boto3.Session().region_name
                )
            )

        # load them in order to have the same data format
        config_data = botocore.configloader.load_config(aws_config.name)
        # now mock out the botocore configuration loader in order to guarantee
        # the correct data is loaded
        with mock.patch('botocore.configloader.load_config') as boto_config:
            boto_config.return_value = config_data

            with open(self.log_config_yaml_profile, 'r') as yaml_input:
                config_yml = yaml_input.read()
                config_dict = yaml.load(config_yml)
                logging.config.dictConfig(config_dict)
                logger = logging.getLogger('root')
                for i in range(10):
                    logger.critical(dict(src="foo3", event=str(i), stack=[1, 2, 3, i], details={}))
                boto_config.assert_called()


if __name__ == "__main__":
    unittest.main()
