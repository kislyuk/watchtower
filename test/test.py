#!/usr/bin/env python3

import json
import logging
import logging.config
import os
import os.path
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from datetime import datetime
from unittest import mock

import boto3
import botocore.configloader
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from watchtower import CloudWatchLogHandler, WatchtowerWarning  # noqa: E402


class TestPyCWL(unittest.TestCase):
    def setUp(self):
        self.test_path = os.path.dirname(__file__)
        self.log_config_yaml_basic = "{}/logging.yml".format(self.test_path)
        self.log_config_yaml_profile = "{}/logging_profile.yml".format(self.test_path)

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

    def _wait_for_log_stream_to_delete(self, log_group, log_stream):
        logs = boto3.client("logs")
        retries = 10
        while retries:
            response = logs.describe_log_streams(
                logGroupName=log_group,
                logStreamNamePrefix=log_stream,
            )
            log_streams = response["logStreams"]
            if log_streams:
                retries -= 1
                time.sleep(0.5)
            else:
                break

        log_streams = [log_streams for stream in log_streams]
        self.assertNotIn(log_stream, log_streams)

    def _wait_for_message(self, message, log_group, log_stream, retries=10):
        logs = boto3.client("logs")
        while retries:
            response = logs.get_log_events(
                logGroupName=log_group,
                logStreamName=log_stream,
            )
            events = response["events"]
            if events:
                messages = [event["message"] for event in events]
                if message in messages:
                    return
            retries -= 1
            time.sleep(0.5)
        else:
            self.fail("Couldn't find message: {} in log stream: {}".format(message, log_stream))

    def test_basic_pycwl_statements(self):
        h = CloudWatchLogHandler()
        loggers = []
        for i in range(5):
            logger = logging.getLogger("logger{}".format(i))
            logger.addHandler(h)
            # logger.addHandler(CloudWatchLogHandler(use_queues=False))
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
        with self.assertWarns(WatchtowerWarning) as cm:
            logger.critical("msg")
        self.assertEqual(
            str(cm.warning),
            "Received message after logging system shutdown",
        )

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
        # FIXME: multiple active CloudWatchLogHandlers cause daemon thread crashes at exit.
        # This can probably be fixed with thread locals.
        pass

    def test_logconfig_dictconfig_basic(self):
        with open(self.log_config_yaml_basic) as yaml_input:
            config_yml = yaml_input.read()
            config_dict = yaml.load(config_yml, Loader=yaml.SafeLoader)
            logging.config.dictConfig(config_dict)
            logger = logging.getLogger("root")
            for i in range(10):
                logger.critical(dict(src="foo2", event=str(i), stack=[1, 2, 3, i], details={}))

    @unittest.skipIf(sys.version_info < (3, 6), "")
    def test_logconfig_dictconfig_profile(self):
        # NOTE: The below is a bit of a hack to get around how Travis CI works so that it
        #   can be fully tested remotely too.

        # save the known configuration values from the ENV vars to a configuration file
        aws_config = tempfile.NamedTemporaryFile()
        with open(aws_config.name, "w") as boto3_config_file:
            boto3_config_file.write("[profile watchtowerlogger]\n")
            boto3_config_file.write("aws_access_key_id={}\n".format(boto3.Session().get_credentials().access_key))
            boto3_config_file.write("aws_secret_access_key={}\n".format(boto3.Session().get_credentials().secret_key))
            boto3_config_file.write("region={}\n".format(boto3.Session().region_name))

        # load them in order to have the same data format
        config_data = botocore.configloader.load_config(aws_config.name)
        # now mock out the botocore configuration loader in order to guarantee
        # the correct data is loaded
        with mock.patch("botocore.configloader.load_config") as boto_config:
            boto_config.return_value = config_data

            with open(self.log_config_yaml_profile) as yaml_input:
                config_yml = yaml_input.read()
                config_dict = yaml.load(config_yml, Loader=yaml.SafeLoader)
                logging.config.dictConfig(config_dict)
                logger = logging.getLogger("root")
                for i in range(10):
                    logger.critical(dict(src="foo3", event=str(i), stack=[1, 2, 3, i], details={}))
                boto_config.assert_called()

    def test_terminating_process(self):
        cwd = os.path.dirname(__file__)
        subprocess.run([sys.executable, "run_logging.py"], cwd=cwd, timeout=10, check=True)

    def test_empty_message(self):
        handler = CloudWatchLogHandler(use_queues=False)
        logger = logging.getLogger("empty")
        logger.addHandler(handler)
        for args in [("",), ("%s", "")]:
            with self.assertWarns(WatchtowerWarning) as cm:
                logger.critical(*args)
            self.assertEqual(
                str(cm.warning), "Received empty message. Empty messages cannot be sent to CloudWatch Logs"
            )

    def test_create_log_stream_on_emit(self):
        log_group = "py_watchtower_test"
        log_stream = str(uuid.uuid4())
        config_dict = self._make_dict_config(
            log_group_name=log_group,
            log_stream_name=log_stream,
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
        create_msg = "foo"
        logger.error(create_msg)
        self._wait_for_message(create_msg, log_group, log_stream)

        with mock.patch("watchtower.CloudWatchLogHandler._idempotent_call") as create_log_stream_mock:
            # Write another message, create stream should not be called here
            logger.error("another")
        create_log_stream_mock.assert_not_called()

        # Delete the log stream, the next write should re-create it
        logs.delete_log_stream(logGroupName=log_group, logStreamName=log_stream)
        self._wait_for_log_stream_to_delete(log_group, log_stream)

        # log and wait for new message to the log stream
        second_create_msg = "This msg should re-create the log stream"
        logger.error(second_create_msg)
        self._wait_for_message(second_create_msg, log_group, log_stream, retries=15)

    def test_existing_log_stream_does_not_create_log_stream(self):
        log_group = "py_watchtower_test"
        log_stream = "existing_" + str(uuid.uuid4())
        logs = boto3.client("logs")
        config_dict = self._make_dict_config(
            log_group_name=log_group,
            log_stream_name=log_stream,
            use_queues=False,
        )
        logging.config.dictConfig(config_dict)
        logger = logging.getLogger("root")

        class h:
            cwl_client = logs

        CloudWatchLogHandler._idempotent_call(h, "create_log_stream", logGroupName=log_group, logStreamName=log_stream)
        self.addCleanup(
            logs.delete_log_stream,
            logGroupName=log_group,
            logStreamName=log_stream,
        )

        with mock.patch("watchtower.CloudWatchLogHandler._idempotent_call") as create_log_stream_mock:
            logger.error("message")

        create_log_stream_mock.assert_not_called()

    def test_handle_error(self):
        logging.config.dictConfig(self._make_dict_config(use_queues=False))
        logger = logging.getLogger("root")
        with mock.patch("watchtower.CloudWatchLogHandler._get_stream_name", side_effect=Exception("test")):
            raise_exceptions = logging.raiseExceptions
            try:
                logging.raiseExceptions = True
                logger.critical("test")
                logging.raiseExceptions = False
                logger.critical("test")
            finally:
                logging.raiseExceptions = raise_exceptions

    @unittest.skipIf(sys.version_info < (3, 8), "Skip test that requires unittest.mock > 3.8")
    def test_formatters(self):
        logging.config.dictConfig(self._make_dict_config(use_queues=False))
        logger = logging.getLogger("root")
        date = datetime.now()
        with mock.patch("watchtower.CloudWatchLogHandler._submit_batch") as submit_batch:
            logger.critical({"date": date})
        submit_batch.assert_called_once()
        self.assertEqual(submit_batch.call_args_list[-1].args[0][0]["message"], json.dumps({"date": date.isoformat()}))

        del logger.handlers[:]
        handler = CloudWatchLogHandler(json_serialize_default=str, use_queues=False)
        logger.addHandler(handler)
        with mock.patch("watchtower.CloudWatchLogHandler._submit_batch") as submit_batch:
            logger.critical({"date": date})
        submit_batch.assert_called_once()
        self.assertEqual(submit_batch.call_args_list[-1].args[0][0]["message"], json.dumps({"date": str(date)}))

        handler.formatter.json_serialize_default = None
        with mock.patch("watchtower.CloudWatchLogHandler._submit_batch") as submit_batch:
            logger.critical({"date": date})
        submit_batch.assert_not_called()  # Error serializing message, caught and printed by logging

        del logger.handlers[:]
        handler = CloudWatchLogHandler(json_serialize_default=str, use_queues=False)
        logger.addHandler(handler)
        handler.formatter.add_log_record_attrs = ["levelname"]
        with mock.patch("watchtower.CloudWatchLogHandler._submit_batch") as submit_batch:
            logger.critical("hello")
            logger.critical({"msg": "hello", "metadata": {"body": b"abc"}})
        self.assertEqual(
            submit_batch.call_args_list[-2].args[0][0]["message"], json.dumps({"msg": "hello", "levelname": "CRITICAL"})
        )
        self.assertEqual(
            submit_batch.call_args_list[-1].args[0][0]["message"],
            json.dumps({"msg": "hello", "metadata": {"body": "b'abc'"}, "levelname": "CRITICAL"}),
        )

    def test_unicode_logging(self):
        handler = CloudWatchLogHandler()
        logger = logging.getLogger("test_unicode")
        logger.addHandler(handler)
        logger.propagate = False

        # 2 byte unicode character, we test with messages above the single message size limit for truncation, and check
        # the total batches submitted. 5 messages of ~256kB has to be split into 2 batches.
        with mock.patch("watchtower.CloudWatchLogHandler._submit_batch") as submit_batch:
            for _ in range(5):
                logger.critical("€" * 1024 * 129)  # intentionally 129 (not 128!)
            handler.flush()

        self.assertEqual(submit_batch.call_count, 2)


if __name__ == "__main__":
    unittest.main()
