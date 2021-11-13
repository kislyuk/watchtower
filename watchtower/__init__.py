from collections.abc import Mapping
from datetime import date, datetime
from operator import itemgetter
import sys, json, logging, time, threading, warnings, functools, platform
import queue

import boto3
import botocore
from botocore.exceptions import ClientError


def _json_serialize_default(o):
    """
    A standard 'default' json serializer function that will serialize datetime objects as ISO format.
    """
    if isinstance(o, (date, datetime)):
        return o.isoformat()


def _boto_debug_filter(record):
    # Filter debug log messages from botocore and its dependency, urllib3.
    # This is required to avoid message storms any time we send logs.
    if record.name.startswith("botocore") and record.levelname == "DEBUG":
        return False
    if record.name.startswith("urllib3") and record.levelname == "DEBUG":
        return False
    return True


def _boto_filter(record):
    # Filter log messages from botocore and its dependency, urllib3.
    # This is required to avoid an infinite loop when shutting down.
    if record.name.startswith("botocore"):
        return False
    if record.name.startswith("urllib3"):
        return False
    return True


class WatchtowerWarning(UserWarning):
    pass


class WatchtowerError(Exception):
    pass


class CloudWatchLogHandler(logging.Handler):
    """
    Create a new CloudWatch log handler object. This is the main entry point to the functionality of the module. See
    http://docs.aws.amazon.com/AmazonCloudWatch/latest/DeveloperGuide/WhatIsCloudWatchLogs.html for more information.

    :param log_group_name:
        Name of the CloudWatch log group to write logs to. By default, the name of this module is used.
    :type log_group_name: String
    :param log_stream_name:
        Name of the CloudWatch log stream to write logs to. By default, a string containing the machine name, the
        program name, and the name of the logger that processed the message is used. Accepts the following format string
        parameters: {machine_name}, {program_name}, {thread_name}, {logger_name}, and {strftime:%m-%d-%y}, where any
        strftime string can be used to include the current UTC datetime in the stream name. The strftime format string
        option can be used to sort logs into streams on an hourly, daily, or monthly basis.
    :type log_stream_name: String
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
    :param boto3_client:
        Client object for sending boto3 logs. Use this to pass custom session or client parameters.

        TODO: document custom credentials, profile name
    :type boto3_client: botocore.client.BaseClient
    :param create_log_group:
        Create CloudWatch Logs log group if it does not exist.  **True** by default.
    :type create_log_group: Boolean
    :param log_group_retention_days:
        Sets the retention policy of the log group in days.  **None** by default.
    :type log_group_retention_days: Integer
    :param create_log_stream:
        Create CloudWatch Logs log stream if it does not exist.  **True** by default.
    :type create_log_stream: Boolean
    :param json_serialize_default:
        The 'default' function to use when serializing dictionaries as JSON. Refer to the Python standard library
        documentation on 'json' for more explanation about the 'default' parameter.
        https://docs.python.org/3/library/json.html#json.dump
        https://docs.python.org/2/library/json.html#json.dump
    :type json_serialize_default: Function
    :param max_message_size:
        Maximum size (in bytes) of a single message.
    :type max_message_size: Integer
    :param endpoint_url:
        The complete URL to use for the constructed client. Normally, botocore will automatically construct
        the appropriate URL to use when communicating with a service. You can specify a complete URL
        (including the "http/https" scheme) to override this behavior.
    :type endpoint_url: String
    """
    END = 1
    FLUSH = 2

    # extra size of meta information with each messages
    EXTRA_MSG_PAYLOAD_SIZE = 26

    def __init__(self,
                 log_group_name: str = __name__,
                 log_stream_name: str = "{machine_name}/{program_name}/{logger_name}",
                 use_queues: bool = True,
                 send_interval: int = 60,
                 max_batch_size: int = 1024 * 1024,
                 max_batch_count: int = 10000,
                 boto3_client: botocore.client.BaseClient = None,
                 boto3_profile_name: str = None,
                 create_log_group: bool = True,
                 log_group_retention_days: int = None,
                 create_log_stream: bool = True,
                 json_serialize_default=None,
                 max_message_size: int = 256 * 1024,
                 log_group=None,
                 stream_name=None,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.log_group_name = log_group_name
        self.log_stream_name = log_stream_name
        self.use_queues = use_queues
        self.send_interval = send_interval
        self.json_serialize_default = json_serialize_default or _json_serialize_default
        self.max_batch_size = max_batch_size
        self.max_batch_count = max_batch_count
        self.max_message_size = max_message_size
        self.create_log_stream = create_log_stream
        self.log_group_retention_days = log_group_retention_days
        self._init_state()

        if log_group is not None:
            if log_group_name != __name__:
                raise WatchtowerError("Both log_group_name and deprecated log_group parameter specified")
            warnings.warn("log_group has been renamed to log_group_name", DeprecationWarning)
            self.log_group_name = log_group
        if stream_name is not None:
            if log_stream_name != "{machine_name}/{program_name}/{logger_name}":
                raise WatchtowerError("Both log_stream_name and deprecated stream_name parameter specified")
            warnings.warn("stream_name has been renamed to log_stream_name", DeprecationWarning)
            self.log_stream_name = stream_name

        self.addFilter(_boto_debug_filter)

        # Creating the client should be the final call in __init__, after all instance attributes are set.
        # This ensures that failing to create the session will not result in any missing attribtues.
        if boto3_client is None and boto3_profile_name is None:
            self.cwl_client = boto3.client("logs")
        elif boto3_client is not None and boto3_profile_name is None:
            self.cwl_client = boto3_client
        elif boto3_client is None and boto3_profile_name is not None:
            self.cwl_client = boto3.session.Session(profile_name=boto3_profile_name).client("logs")
        else:
            raise WatchtowerError("Either boto3_client or boto3_profile_name can be specified, but not both")

        if create_log_group:
            self._ensure_log_group()

        if log_group_retention_days:
            self._idempotent_call("put_retention_policy",
                                  logGroupName=self.log_group_name,
                                  retentionInDays=self.log_group_retention_days)

    def _at_fork_reinit(self):
        # This was added in Python 3.9 and should only be called with a recent
        # version of Python. An older version will attempt to call createLock
        # instead.
        super()._at_fork_reinit()
        self._init_state()

    def _init_state(self):
        self.queues, self.sequence_tokens = {}, {}
        self.threads = []
        self.creating_log_stream, self.shutting_down = False, False

    def _paginate(self, boto3_paginator, *args, **kwargs):
        for page in boto3_paginator.paginate(*args, **kwargs):
            for result_key in boto3_paginator.result_keys:
                for value in page.get(result_key.parsed.get("value"), []):
                    yield value

    def _ensure_log_group(self):
        try:
            paginator = self.cwl_client.get_paginator("describe_log_groups")
            for log_group in self._paginate(paginator, logGroupNamePrefix=self.log_group_name):
                if log_group["logGroupName"] == self.log_group_name:
                    return
        except self.cwl_client.exceptions.ClientError:
            pass
        self._idempotent_call("create_log_group", logGroupName=self.log_group_name)

    def _idempotent_call(self, method, *args, **kwargs):
        method_callable = getattr(self.cwl_client, method)
        try:
            method_callable(*args, **kwargs)
        except (self.cwl_client.exceptions.OperationAbortedException,
                self.cwl_client.exceptions.ResourceAlreadyExistsException):
            pass

    @functools.lru_cache(maxsize=0)
    def _get_machine_name(self):
        return platform.node()

    def _get_stream_name(self, message):
        return self.log_stream_name.format(
            machine_name=self._get_machine_name(),
            program_name=sys.argv[0],
            thread_name=threading.current_thread().name,
            logger_name=message.name,
            strftime=datetime.utcnow()
        )

    def _submit_batch(self, batch, log_stream_name, max_retries=5):
        if len(batch) < 1:
            return
        sorted_batch = sorted(batch, key=itemgetter('timestamp'), reverse=False)
        kwargs = dict(logGroupName=self.log_group_name, logStreamName=log_stream_name,
                      logEvents=sorted_batch)
        if self.sequence_tokens[log_stream_name] is not None:
            kwargs["sequenceToken"] = self.sequence_tokens[log_stream_name]
        response = None

        for retry in range(max_retries):
            try:
                response = self.cwl_client.put_log_events(**kwargs)
                break
            except ClientError as e:
                if isinstance(e, (self.cwl_client.exceptions.DataAlreadyAcceptedException,
                                  self.cwl_client.exceptions.InvalidSequenceTokenException)):
                    next_expected_token = e.response["Error"]["Message"].rsplit(" ", 1)[-1]
                    # null as the next sequenceToken means don't include any
                    # sequenceToken at all, not that the token should be set to "null"
                    if next_expected_token == "null":
                        kwargs.pop("sequenceToken", None)
                    else:
                        kwargs["sequenceToken"] = next_expected_token
                elif isinstance(e, self.cwl_client.exceptions.ResourceNotFoundException):
                    if self.create_log_stream:
                        self.creating_log_stream = True
                        try:
                            self._idempotent_call("create_log_stream",
                                                  logGroupName=self.log_group_name,
                                                  logStreamName=log_stream_name)
                            # We now have a new stream name and the next retry
                            # will be the first attempt to log to it, so we
                            # should not continue to use the old sequence token
                            # at this point, the first write to the new stream
                            # should not contain a sequence token at all.
                            kwargs.pop("sequenceToken", None)
                        finally:
                            self.creating_log_stream = False
                else:
                    warnings.warn("Failed to deliver logs: {}".format(e), WatchtowerWarning)
            except Exception as e:
                warnings.warn("Failed to deliver logs: {}".format(e), WatchtowerWarning)

        # response can be None only when all retries have been exhausted
        if response is None or "rejectedLogEventsInfo" in response:
            warnings.warn("Failed to deliver logs: {}".format(response), WatchtowerWarning)
        elif "nextSequenceToken" in response:
            # According to https://github.com/kislyuk/watchtower/issues/134, nextSequenceToken may sometimes be absent
            # from the response
            self.sequence_tokens[log_stream_name] = response["nextSequenceToken"]

    def createLock(self):
        super().createLock()
        self._init_state()

    def emit(self, message):
        if self.creating_log_stream:
            return  # Avoid infinite recursion when asked to log a message as our own side effect

        if message.msg == "":
            warnings.warn("Received empty message. Empty messages cannot be sent to CloudWatch Logs", WatchtowerWarning)

        stream_name = self._get_stream_name(message)

        if stream_name not in self.sequence_tokens:
            self.sequence_tokens[stream_name] = None

        if isinstance(message.msg, Mapping):
            message.msg = json.dumps(message.msg, default=self.json_serialize_default)

        cwl_message = dict(timestamp=int(message.created * 1000), message=self.format(message))

        if self.use_queues:
            if stream_name not in self.queues:
                self.queues[stream_name] = queue.Queue()
                thread = threading.Thread(target=self._dequeue_batch,
                                          args=(self.queues[stream_name], stream_name, self.send_interval,
                                                self.max_batch_size, self.max_batch_count, self.max_message_size))
                self.threads.append(thread)
                thread.daemon = True
                thread.start()
            if self.shutting_down:
                warnings.warn("Received message after logging system shutdown", WatchtowerWarning)
            else:
                self.queues[stream_name].put(cwl_message)
        else:
            self._submit_batch([cwl_message], stream_name)

    def _dequeue_batch(self, my_queue, stream_name, send_interval, max_batch_size, max_batch_count, max_message_size):
        msg = None
        max_message_body_size = max_message_size - CloudWatchLogHandler.EXTRA_MSG_PAYLOAD_SIZE

        def size(_msg):
            return (len(_msg["message"]) if isinstance(_msg, dict) else 1) + CloudWatchLogHandler.EXTRA_MSG_PAYLOAD_SIZE

        def truncate(_msg2):
            warnings.warn("Log message size exceeds CWL max payload size, truncated", WatchtowerWarning)
            _msg2["message"] = _msg2["message"][:max_message_body_size]
            return _msg2

        # See https://boto3.readthedocs.io/en/latest/reference/services/logs.html#CloudWatchLogs.Client.put_log_events
        while msg != self.END:
            cur_batch = [] if msg is None or msg == self.FLUSH else [msg]
            cur_batch_size = sum(map(size, cur_batch))
            cur_batch_msg_count = len(cur_batch)
            cur_batch_deadline = time.time() + send_interval
            while True:
                try:
                    msg = my_queue.get(block=True, timeout=max(0, cur_batch_deadline - time.time()))
                    if size(msg) > max_message_body_size:
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
        """
        Send any queued messages to CloudWatch. This method does nothing if ``use_queues`` is set to False.
        """
        # fixme: don't add filter if it's already installed
        self.addFilter(_boto_filter)
        if self.shutting_down:
            return
        for q in self.queues.values():
            q.put(self.FLUSH)
        for q in self.queues.values():
            q.join()

    def close(self):
        """
        Send any queued messages to CloudWatch and prevent further processing of messages.
        This method does nothing if ``use_queues`` is set to False.
        """
        # fixme: don't add filter if it's already installed
        self.addFilter(_boto_filter)
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
        super().close()
