import os, sys, json, logging

import boto3
from botocore.exceptions import ClientError

#logging.basicConfig(level=logging.ERROR)
#logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
#logging.getLogger("botocore.vendored.requests").setLevel(logging.DEBUG)

#response = client.create_trail(Name=__name__, S3BucketName=__name__)

handler_base_class = logging.Handler

def _idempotent_create(_callable, *args, **kwargs):
    try:
        _callable(*args, **kwargs)
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") != "ResourceAlreadyExistsException":
            raise

class CloudWatchLogHandler(handler_base_class):
    """
    Create a new CloudWatch log handler object. This is the main entry point to the functionality of the module.
    :param log_group: TODO
    :type log_group: String
    :param queue: TODO
    :type queue: Boolean
    :param send_interval:
        Maximum time (in seconds, or a timedelta (TODO)) to hold messages in queue before sending a batch
    :type send_interval: Integer
    """
    def __init__(self, log_group=__name__, queue=True, send_interval=60, *args, **kwargs):
        handler_base_class.__init__(self, *args, **kwargs)
        self.log_group = log_group
        self.queue = queue
        self.send_interval = send_interval
        self.cwl_client = boto3.client('logs')
        self.cwl_stream_sequence_tokens = {}
        _idempotent_create(self.cwl_client.create_log_group, logGroupName=self.log_group)

    def _submit_batch(self, batch, stream_name):
        kwargs = dict(logGroupName=self.log_group, logStreamName=stream_name,
                      logEvents=batch)
        if self.cwl_stream_sequence_tokens[stream_name] is not None:
            kwargs["sequenceToken"] = self.cwl_stream_sequence_tokens[stream_name]

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

        self.cwl_stream_sequence_tokens[stream_name] = response["nextSequenceToken"]

    def emit(self, message):
        #print("Will emit", message)
        #print(message.__dict__)

        stream_name = message.name
        if stream_name not in self.cwl_stream_sequence_tokens:
            _idempotent_create(self.cwl_client.create_log_stream,
                               logGroupName=self.log_group, logStreamName=stream_name)
            self.cwl_stream_sequence_tokens[stream_name] = None

        batch = [dict(timestamp=int(message.created * 1000), message=message.msg)]
        self._submit_batch(batch, stream_name)

"""
use async? probably not - no way to guarantee wake time

use multiprocessing.queue?

"""
