from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys, json, logging, time, threading, warnings, collections

try:
    import Queue
except ImportError:
    import queue as Queue

from eight import *

import boto3
from botocore.exceptions import ClientError

handler_base_class = logging.Handler

def _idempotent_create(_callable, *args, **kwargs):
    try:
        _callable(*args, **kwargs)
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") != "ResourceAlreadyExistsException":
            raise

class PyCWLWarning(UserWarning):
    pass

class CloudWatchLogHandler(handler_base_class):
    """
    Create a new CloudWatch log handler object. This is the main entry point to the functionality of the module. See
    http://docs.aws.amazon.com/AmazonCloudWatch/latest/DeveloperGuide/WhatIsCloudWatchLogs.html for more information.

    :param log_group: Name of the CloudWatch log group to write logs to.
    :type log_group: String
    :param use_queues:
        If **True**, logs will be queued on a per-stream basis and sent in batches. To manage the queues, a queue
        handler thread will be spawned.
    :type queue: Boolean
    :param send_interval:
        Maximum time (in seconds, or a timedelta) to hold messages in queue before sending a batch.
    :type send_interval: Integer
    :param max_batch_size:
        Maximum size (in bytes) of the queue before sending a batch. From CloudWatch Logs documentation: **The maximum
        batch size is 1,048,576 bytes, and this size is calculated as the sum of all event messages in UTF-8, plus 26
        bytes for each log event.**
    :type max_batch_size: Integer
    :param max_batch_count:
        Maximum number of messages in the queue before sending a batch. From CloudWatch Logs documentation: **The
        maximum number of log events in a batch is 10,000.**
    :type max_batch_count: Integer
    """
    END = 1

    def __init__(self, log_group=__name__, use_queues=True, send_interval=60, max_batch_size=1024*1024,
                 max_batch_count=10000, *args, **kwargs):
        handler_base_class.__init__(self, *args, **kwargs)
        self.log_group = log_group
        self.use_queues = use_queues
        self.send_interval = send_interval
        self.max_batch_size = max_batch_size
        self.max_batch_count = max_batch_count
        self.cwl_client = boto3.client("logs")
        self.queues, self.sequence_tokens = {}, {}
        self.threads = []
        self.shutting_down = False
        _idempotent_create(self.cwl_client.create_log_group, logGroupName=self.log_group)

    def _submit_batch(self, batch, stream_name):
        if len(batch) < 1:
            return
        kwargs = dict(logGroupName=self.log_group, logStreamName=stream_name,
                      logEvents=batch)
        if self.sequence_tokens[stream_name] is not None:
            kwargs["sequenceToken"] = self.sequence_tokens[stream_name]

        try:
            response = self.cwl_client.put_log_events(**kwargs)
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") in ("DataAlreadyAcceptedException",
                                                           "InvalidSequenceTokenException"):
                kwargs["sequenceToken"] = e.response["Error"]["Message"].rsplit(" ", 1)[-1]
                response = self.cwl_client.put_log_events(**kwargs)
            else:
                raise

        if "rejectedLogEventsInfo" in response:
            # TODO: make this configurable/non-fatal
            raise Exception("Failed to deliver logs: {}".format(response))

        self.sequence_tokens[stream_name] = response["nextSequenceToken"]

    def emit(self, message):
        stream_name = message.name
        if stream_name not in self.sequence_tokens:
            _idempotent_create(self.cwl_client.create_log_stream,
                               logGroupName=self.log_group, logStreamName=stream_name)
            self.sequence_tokens[stream_name] = None

        msg = dict(timestamp=int(message.created * 1000), message=self.format(message))
        if isinstance(msg["message"], collections.Mapping):
            msg["message"] = json.dumps(msg["message"])
        if self.use_queues:
            if stream_name not in self.queues:
                self.queues[stream_name] = Queue.Queue()
                thread = threading.Thread(target=self.batch_sender,
                                          args=(self.queues[stream_name], stream_name, self.send_interval,
                                                self.max_batch_size, self.max_batch_count))
                self.threads.append(thread)
                thread.daemon = True
                thread.start()
            if self.shutting_down:
                warnings.warn("Received message after logging system shutdown", PyCWLWarning)
            else:
                self.queues[stream_name].put(msg)
        else:
            self._submit_batch([msg], stream_name)

    def batch_sender(self, my_queue, stream_name, send_interval, max_batch_size, max_batch_count):
        #thread_local = threading.local()
        msg = None
        def size(msg):
            return len(msg["message"]) + 26

        # See https://boto3.readthedocs.org/en/latest/reference/services/logs.html#logs.Client.put_log_events
        while msg != self.END:
            cur_batch = [] if msg is None else [msg]
            cur_batch_size = sum(size(msg) for msg in cur_batch)
            cur_batch_msg_count = len(cur_batch)
            cur_batch_deadline = time.time() + send_interval
            while True:
                try:
                    msg = my_queue.get(block=True, timeout=max(0, cur_batch_deadline-time.time()))
                except Queue.Empty:
                    # If the queue is empty, we don't want to reprocess the previous message
                    msg = None
                if msg is None \
                   or msg == self.END \
                   or cur_batch_size + size(msg) > max_batch_size \
                   or cur_batch_msg_count >= max_batch_count \
                   or time.time() >= cur_batch_deadline:
                    self._submit_batch(cur_batch, stream_name)
                    if msg is not None:
                        # We don't want to call task_done if the queue was empty and we didn't receive anything new
                        my_queue.task_done()
                    break
                elif msg:
                    cur_batch_size += size(msg)
                    cur_batch_msg_count += 1
                    cur_batch.append(msg)
                    my_queue.task_done()

    def flush(self):
        self.shutting_down = True
        for q in self.queues.values():
            q.put(self.END)
        for q in self.queues.values():
            q.join()
