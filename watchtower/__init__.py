from __future__ import absolute_import, division, print_function, unicode_literals
from operator import itemgetter
import os, sys, json, logging, time, threading, warnings, collections

try:
    import queue
except ImportError:
    import Queue as queue

import boto3
import boto3.session
from botocore.exceptions import ClientError

handler_base_class = logging.Handler

def _idempotent_create(_callable, *args, **kwargs):
    try:
        _callable(*args, **kwargs)
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") != "ResourceAlreadyExistsException":
            raise

class WatchtowerWarning(UserWarning):
    pass

class CloudWatchLogHandler(handler_base_class):
    """
    Create a new CloudWatch log handler object. This is the main entry point to the functionality of the module. See
    http://docs.aws.amazon.com/AmazonCloudWatch/latest/DeveloperGuide/WhatIsCloudWatchLogs.html for more information.

    :param log_group: Name of the CloudWatch log group to write logs to. By default, the name of this module is used.
    :type log_group: String
    :param stream_name:
        Name of the CloudWatch log stream to write logs to. By default, the name of the logger that processed the
        message is used. Accepts a format string parameter of {logger_name}.
    :type stream_name: String
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
    :param boto3_session:
        Session object to create boto3 `logs` clients. Accepts AWS credential, profile_name, and region_name from its
        constructor.
    :type boto3_session: boto3.session.Session
    :param create_log_group:
        Create log group.  **True** by default.
    :type create_log_group: Boolean
    """
    END = 1
    FLUSH = 2

    # extra size of meta information with each messages
    EXTRA_MSG_PAYLOAD_SIZE = 26

    @staticmethod
    def _get_session(boto3_session, boto3_profile_name):
        if boto3_session:
            return boto3_session

        if boto3_profile_name:
            return boto3.session.Session(profile_name=boto3_profile_name)

        return boto3

    def __init__(self, log_group=__name__, stream_name=None, use_queues=True, send_interval=60,
                 max_batch_size=1024*1024, max_batch_count=10000, boto3_session=None,
                 boto3_profile_name=None, create_log_group=True, *args, **kwargs):
        handler_base_class.__init__(self, *args, **kwargs)
        self.log_group = log_group
        self.stream_name = stream_name
        self.use_queues = use_queues
        self.send_interval = send_interval
        self.max_batch_size = max_batch_size
        self.max_batch_count = max_batch_count
        self.queues, self.sequence_tokens = {}, {}
        self.threads = []
        self.shutting_down = False
        self.cwl_client = self._get_session(
            boto3_session, boto3_profile_name
        ).client("logs")
        if create_log_group:
            _idempotent_create(self.cwl_client.create_log_group,
                               logGroupName=self.log_group)

    def _submit_batch(self, batch, stream_name, max_retries=5):
        if len(batch) < 1:
            return
        sorted_batch = sorted(batch, key=itemgetter('timestamp'), reverse=False)
        kwargs = dict(logGroupName=self.log_group, logStreamName=stream_name,
                      logEvents=sorted_batch)
        if self.sequence_tokens[stream_name] is not None:
            kwargs["sequenceToken"] = self.sequence_tokens[stream_name]
        response = None

        for retry in range(max_retries):
            try:
                response = self.cwl_client.put_log_events(**kwargs)
                break
            except ClientError as e:
                if e.response.get("Error", {}).get("Code") in ("DataAlreadyAcceptedException",
                                                               "InvalidSequenceTokenException"):
                    kwargs["sequenceToken"] = e.response["Error"]["Message"].rsplit(" ", 1)[-1]
                else:
                    warnings.warn("Failed to deliver logs: {}".format(e), WatchtowerWarning)
            except Exception as e:
                warnings.warn("Failed to deliver logs: {}".format(e), WatchtowerWarning)

        # response can be None only when all retries have been exhausted
        if response is None or "rejectedLogEventsInfo" in response:
            warnings.warn("Failed to deliver logs: {}".format(response), WatchtowerWarning)

    def emit(self, message):
        stream_name = self.stream_name
        if stream_name is None:
            stream_name = message.name
        else:
            stream_name = stream_name.format(logger_name=message.name)
        if stream_name not in self.sequence_tokens:
            _idempotent_create(self.cwl_client.create_log_stream,
                               logGroupName=self.log_group, logStreamName=stream_name)
            self.sequence_tokens[stream_name] = None

        if isinstance(message.msg, collections.Mapping):
            message.msg = json.dumps(message.msg)

        cwl_message = dict(timestamp=int(message.created * 1000), message=self.format(message))

        if self.use_queues:
            if stream_name not in self.queues:
                self.queues[stream_name] = queue.Queue()
                thread = threading.Thread(target=self.batch_sender,
                                          args=(self.queues[stream_name], stream_name, self.send_interval,
                                                self.max_batch_size, self.max_batch_count))
                self.threads.append(thread)
                thread.daemon = True
                thread.start()
            if self.shutting_down:
                warnings.warn("Received message after logging system shutdown", WatchtowerWarning)
            else:
                self.queues[stream_name].put(cwl_message)
        else:
            self._submit_batch([cwl_message], stream_name)

    def batch_sender(self, my_queue, stream_name, send_interval, max_batch_size, max_batch_count):
        #thread_local = threading.local()
        msg = None

        def size(_msg):
            return (len(_msg["message"]) if isinstance(_msg, dict) else 1) + CloudWatchLogHandler.EXTRA_MSG_PAYLOAD_SIZE

        def truncate(_msg2):
            warnings.warn("Log message size exceeds CWL max payload size, truncated", WatchtowerWarning)
            _msg2["message"] = _msg2["message"][:max_batch_size-CloudWatchLogHandler.EXTRA_MSG_PAYLOAD_SIZE]
            return _msg2

        # See https://boto3.readthedocs.io/en/latest/reference/services/logs.html#CloudWatchLogs.Client.put_log_events
        while msg != self.END:
            cur_batch = [] if msg is None or msg == self.FLUSH else [msg]
            cur_batch_size = sum(size(msg) for msg in cur_batch)
            cur_batch_msg_count = len(cur_batch)
            cur_batch_deadline = time.time() + send_interval
            while True:
                try:
                    msg = my_queue.get(block=True, timeout=max(0, cur_batch_deadline-time.time()))
                    if size(msg) > max_batch_size:
                        msg = truncate(msg)
                except queue.Empty:
                    # If the queue is empty, we don't want to reprocess the previous message
                    msg = None
                if msg is None \
                   or msg == self.END \
                   or msg == self.FLUSH \
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
        if self.shutting_down:
            return
        for q in self.queues.values():
            q.put(self.FLUSH)
        for q in self.queues.values():
            q.join()

    def close(self):
        # Avoid waiting on the queue again when the close called twice.
        # Otherwise the second call, as no thread is running, it will hang
        # forever
        if self.shutting_down:
            return
        self.shutting_down = True
        for q in self.queues.values():
            q.put(self.END)
        for q in self.queues.values():
            q.join()
        handler_base_class.close(self)
