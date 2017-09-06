# coding: utf-8
import boto3
from django.conf import settings
from watchtower import CloudWatchLogHandler


class DjangoCloudWatchLogHandler(CloudWatchLogHandler):
    """
    Use the AWS variable configurations from the django settings.
    """

    def __init__(self, *args, **kwargs):

        client_kwargs = {}
        if hasattr(settings, 'AWS_ACCESS_KEY_ID'):
            client_kwargs.update({
                'aws_access_key_id': getattr(settings, 'AWS_ACCESS_KEY_ID'),
            })

        if hasattr(settings, 'AWS_SECRET_ACCESS_KEY'):
            client_kwargs.update({
                'aws_secret_access_key': getattr(settings, 'AWS_SECRET_ACCESS_KEY'),
            })

        if hasattr(settings, 'AWS_DEFAULT_REGION'):
            client_kwargs.update({
                'region_name': getattr(settings, 'AWS_DEFAULT_REGION'),
            })

        kwargs['boto3_session'] = boto3.session.Session(**client_kwargs)

        super(DjangoCloudWatchLogHandler, self).__init__(*args, **kwargs)
