#!/usr/bin/env python3
# coding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

import collections
import copy
from datetime import datetime

import mock
import logging
import logging.config
import os
import os.path
import re
import sys
import tempfile
import time
import unittest
import subprocess
import uuid

import boto3
import botocore.configloader
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  # noqa
from watchtower import CloudWatchLogHandler, _idempotent_create

USING_PYTHON2 = True if sys.version_info < (3, 0) else False


class TestPyCWL(unittest.TestCase):
    def setUp(self):
        self.test_path = os.path.dirname(__file__)
        self.log_config_yaml_basic = '{0}/logging.yml'.format(self.test_path)
        self.log_config_yaml_profile = '{0}/logging_profile.yml'.format(self.test_path)

    @staticmethod
    def _make_dict_config(**handler_props):
        return {
            "version": 1,
            "handlers": {
                "watchtower": {
                    "()": "watchtower.CloudWatchLogHandler",
                    **handler_props,
                },
            },
            "loggers": {
                "root": {
                    "handlers": ["watchtower"],
                },
            },
        }

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

    def test_json_logging_object_with_datetime(self):
        handler = CloudWatchLogHandler()
        logger = logging.getLogger("json")
        logger.addHandler(handler)
        for i in range(10):
            logger.critical(dict(src="foo", event=str(i), stack=[1, 2, 3, i], details=dict(time=datetime(2019, 1, 1))))

    def test_multiple_handlers(self):
        # FIXME: multiple active CloudWatchLogHandlers cause daemon thread crashes at exit. This can probably be fixed with thread locals.
        pass

    def test_logconfig_dictconfig_basic(self):
        with open(self.log_config_yaml_basic, 'r') as yaml_input:
            config_yml = yaml_input.read()
            config_dict = yaml.load(config_yml, Loader=yaml.SafeLoader)
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
                config_dict = yaml.load(config_yml, Loader=yaml.SafeLoader)
                logging.config.dictConfig(config_dict)
                logger = logging.getLogger('root')
                for i in range(10):
                    logger.critical(dict(src="foo3", event=str(i), stack=[1, 2, 3, i], details={}))
                boto_config.assert_called()

    def test_terminating_process(self):
        cwd = os.path.dirname(__file__)
        proc = subprocess.Popen(['python', 'run_logging.py'], cwd=cwd)
        proc.wait() if USING_PYTHON2 else proc.wait(10)

    def test_empty_message(self):
        handler = CloudWatchLogHandler(use_queues=False)
        logger = logging.getLogger("empty")
        logger.addHandler(handler)
        logger.critical("")

    def test_create_log_stream_on_emit(self):
        log_group = "py_watchtower_test"
        log_stream = str(uuid.uuid4())
        config_dict = self._make_dict_config(
            log_group=log_group,
            stream_name=log_stream,
            use_queues=False,
        )
        logging.config.dictConfig(config_dict)
        logger = logging.getLogger("root")
        logs = boto3.client("logs")
        self.addCleanup(
            logs.delete_log_stream,
            logGroupName=log_group,
            logStreamName=log_stream,
        )

        # Log stream does not exist at this point, emitting a record creates it.
        logger.error("foo")

        # Wait until message appears in log stream.
        logs = boto3.client("logs")
        retries = 10
        while True:
            response = logs.get_log_events(
                logGroupName=log_group,
                logStreamName=log_stream,
            )
            events = response["events"]
            if not events:
                retries -= 1
                time.sleep(0.5)
            else:
                break

        [event] = events
        self.assertEqual(event["message"], "foo")

        with mock.patch("watchtower._idempotent_create") as create_log_stream_mock:
            logger.error("another")
        create_log_stream_mock.assert_not_called()

    def test_existing_log_stream_does_not_create_log_stream(self):
        log_group = "py_watchtower_test"
        log_stream = "existing_stream"
        logs = boto3.client("logs")
        config_dict = self._make_dict_config(
            log_group=log_group,
            stream_name=log_stream,
            use_queues=False,
        )
        logging.config.dictConfig(config_dict)
        logger = logging.getLogger("root")
        _idempotent_create(logs.create_log_stream, logGroupName=log_group, logStreamName=log_stream)
        self.addCleanup(
            logs.delete_log_stream,
            logGroupName=log_group,
            logStreamName=log_stream,
        )

        with mock.patch("watchtower._idempotent_create") as create_log_stream_mock:
            logger.error("message")

        create_log_stream_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
