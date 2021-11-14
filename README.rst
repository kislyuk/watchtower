Watchtower: Python CloudWatch Logging
=====================================
Watchtower is a log handler for `Amazon Web Services CloudWatch Logs
<https://aws.amazon.com/blogs/aws/cloudwatch-log-service/>`_.

CloudWatch Logs is a log management service built into AWS. It is conceptually similar to services like Splunk, Datadog,
and Loggly, but is more lightweight, cheaper, and tightly integrated with the rest of AWS.

Watchtower, in turn, is a lightweight adapter between the `Python logging system
<https://docs.python.org/library/logging.html>`_ and CloudWatch Logs. It uses the `boto3 AWS SDK
<https://github.com/boto/boto3>`_, and lets you plug your application logging directly into CloudWatch without the need
to install a system-wide log collector like `awscli-cwlogs <https://pypi.python.org/pypi/awscli-cwlogs>`_ and round-trip
your logs through the instance's syslog. It aggregates logs into batches to avoid sending an API request per each log
message, while guaranteeing a delivery deadline (60 seconds by default).

Installation
~~~~~~~~~~~~
::

    pip install watchtower

Synopsis
~~~~~~~~
Install `awscli <https://pypi.python.org/pypi/awscli>`_ and set your AWS credentials (run ``aws configure``).

.. code-block:: python

    import watchtower, logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.addHandler(watchtower.CloudWatchLogHandler())
    logger.info("Hi")
    logger.info(dict(foo="bar", details={}))

After running the example, you can see the log output in your `AWS console
<https://console.aws.amazon.com/cloudwatch/home>`_.

IAM permissions
~~~~~~~~~~~~~~~
The process running watchtower needs to have access to IAM credentials to call the CloudWatch Logs API. The process
for loading and configuring credentials is described in the
`Boto3 Credentials documentation <https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html>`_.
When running Watchtower on an EC2 instance or other AWS compute resource, boto3 automatically loads credentials from
`instance metadata <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html>`_ or container
credentials provider (AWS_WEB_IDENTITY_TOKEN_FILE or AWS_CONTAINER_CREDENTIALS_FULL_URI). The easiest way to grant the
right permissions to the IAM role associated with these credentials is by attaching an AWS
`managed IAM policy <https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_managed-vs-inline.html>`_ to the
role. While AWS provides no generic managed CloudWatch Logs writer policy, it is recommended that you use the
``arn:aws:iam::aws:policy/AWSOpsWorksCloudWatchLogs`` managed policy, which has just the right permissions without being
overly broad.

Example: Flask logging with Watchtower
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import watchtower, flask, logging

    logging.basicConfig(level=logging.INFO)
    app = flask.Flask("loggable")
    handler = watchtower.CloudWatchLogHandler()
    app.logger.addHandler(handler)
    logging.getLogger("werkzeug").addHandler(handler)

    @app.route('/')
    def hello_world():
        return 'Hello World!'

    if __name__ == '__main__':
        app.run()

(See also `http://flask.pocoo.org/docs/errorhandling/ <http://flask.pocoo.org/docs/errorhandling/>`_.)

Example: Django logging with Watchtower
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This is an example of Watchtower integration with Django. In your Django project, add the following to ``settings.py``:

.. code-block:: python

    import boto3

    AWS_REGION_NAME = 'your region'

    boto3_logs_client = boto3.client("logs", region_name=AWS_REGION_NAME)

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'root': {
            'level': logging.ERROR,
            'handlers': ['console'],
        },
        'formatters': {
            'simple': {
                'format': "%(asctime)s [%(levelname)-8s] %(message)s",
                'datefmt': "%Y-%m-%d %H:%M:%S"
            },
            'aws': {
                # you can add specific format for aws here
                'format': "%(asctime)s [%(levelname)-8s] %(message)s",
                'datefmt': "%Y-%m-%d %H:%M:%S"
            },
        },
        'handlers': {
            'watchtower': {
                'level': 'DEBUG',
                'class': 'watchtower.CloudWatchLogHandler',
                'boto3_client': boto3_logs_client,
                'log_group_name': 'MyLogGroupName',
                'log_stream_name': 'MyStreamName',
                'formatter': 'aws',
            },
        },
        'loggers': {
            'django': {
                'level': 'INFO',
                'handlers': ['watchtower'],
                'propagate': False,
            },
            # add your other loggers here...
        },
    }

Using this configuration, every log statement from Django will be sent to Cloudwatch in the log group ``MyLogGroupName``
under the stream name ``MyStreamName``. Instead of setting credentials via ``AWS_ACCESS_KEY_ID`` and other variables
in ``settings.py``, it is recommended that you assign an IAM role to your instance, prompting boto3 to automatically
ingest IAM role credentials from
`instance metadata <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html>`_.

(See also the `Django logging documentation <https://docs.djangoproject.com/en/dev/topics/logging/>`_.)

Examples: Querying CloudWatch logs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This section is not specific to Watchtower. It demonstrates the use of awscli and jq to read and search CloudWatch logs
on the command line.

For the Flask example above, you can retrieve your application logs with the following two commands::

    aws logs get-log-events --log-group-name watchtower --log-stream-name loggable | jq '.events[].message'
    aws logs get-log-events --log-group-name watchtower --log-stream-name werkzeug | jq '.events[].message'

In addition to the raw get-log-events API, CloudWatch Logs supports
`extraction of your logs into an S3 bucket <https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/S3Export.html>`_,
`log analysis with a query language <https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html>`_,
and alerting and dashboards based on `metric filters
<http://docs.aws.amazon.com/AmazonCloudWatch/latest/DeveloperGuide/FilterAndPatternSyntax.html>`_, which are pattern
rules that extract information from your logs and feed it to alarms and dashboard graphs. If you want to make use of
these features on the command line, the author of Watchtower has a toolkit called
`aegea <https://github.com/kislyuk/aegea>`_ that includes the commands ``aegea logs`` and ``aegea grep`` to easily
access the S3 Export and Insights features.

Examples: Python Logging Config
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Python ``logging.config`` module has the ability to provide a configuration file that can be loaded in order to
separate the logging configuration from the code.

The following are two example YAML configuration files that can be loaded using PyYAML. The resulting ``dict`` object
can then be loaded into ``logging.config.dictConfig``. The first example is a basic example that relies on the default
configuration provided by ``boto3``:

.. code-block:: yaml

    # Default AWS Config
    version: 1
    disable_existing_loggers: False
    formatters:
      json:
        format: "[%(asctime)s] %(process)d %(levelname)s %(name)s:%(funcName)s:%(lineno)s - %(message)s"
      plaintext:
        format: "[%(asctime)s] %(process)d %(levelname)s %(name)s:%(funcName)s:%(lineno)s - %(message)s"
    handlers:
      console:
        class: logging.StreamHandler
        formatter: plaintext
        level: DEBUG
        stream: ext://sys.stdout
      logfile:
        class: logging.handlers.RotatingFileHandler
        formatter: plaintext
        level: DEBUG
        filename: watchtower.log
        maxBytes: 1000000
        backupCount: 3
      watchtower:
        class: watchtower.CloudWatchLogHandler
        formatter: json
        level: DEBUG
        log_group_name: watchtower
        log_stream_name: "{logger_name}-{strftime:%y-%m-%d}"
        send_interval: 10
        create_log_group: False
    root:
      level: DEBUG
      propagate: True
      handlers: [console, logfile, watchtower]
    loggers:
      botocore:
        level: INFO
      urllib3:
        level: INFO

The above works well if you can use the default boto3 credential configuration, or rely on environment variables.
However, sometimes one may want to use different credentials for logging than used for other functionality;
in this case the ``boto3_profile_name`` option to Watchtower can be used to provide a boto3 profile name:

.. code-block:: yaml

    # AWS Config Profile
    version: 1
    ...
    handlers:
      ...
      watchtower:
        boto3_profile_name: watchtowerlogger
        ...

Finally, the following shows how to load the configuration into the working application:

.. code-block:: python

    import logging.config

    import flask
    import yaml

    app = flask.Flask("loggable")

    @app.route('/')
    def hello_world():
        return 'Hello World!'

    if __name__ == '__main__':
        with open('logging.yml') as log_config:
            config_yml = log_config.read()
            config_dict = yaml.safe_load(config_yml)
            logging.config.dictConfig(config_dict)
            app.run()

Boto3/botocore/urllib3 logs
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Because watchtower uses boto3 to send logs, the act of sending them generates a number of DEBUG level log messages
from boto3's dependencies, botocore and urllib3. To avoid generating a self-perpetuating stream of log messages,
``watchtower.CloudWatchLogHandler`` attaches a
`filter <https://docs.python.org/3/library/logging.html#logging.Handler.addFilter>`_ to itself which drops all DEBUG
level messages from these libraries, and drops all messages at all levels from them when shutting down (specifically,
in ``watchtower.CloudWatchLogHandler.flush()`` and ``watchtower.CloudWatchLogHandler.close()``). The filter does not
apply to any other handlers you may have processing your messages, so the following basic configuration will cause
botocore debug logs to print to stderr but not to Cloudwatch:

.. code-block:: python

    import watchtower, logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()
    logger.addHandler(watchtower.CloudWatchLogHandler())

Authors
~~~~~~~
* Andrey Kislyuk

Links
~~~~~
* `Project home page (GitHub) <https://github.com/kislyuk/watchtower>`_
* `Documentation <https://kislyuk.github.io/watchtower/>`_
* `Package distribution (PyPI) <https://pypi.python.org/pypi/watchtower>`_
* `AWS CLI CloudWatch Logs plugin <https://pypi.python.org/pypi/awscli-cwlogs>`_
* `Docker awslogs adapter <https://github.com/docker/docker/blob/master/daemon/logger/awslogs/cloudwatchlogs.go>`_

Bugs
~~~~
Please report bugs, issues, feature requests, etc. on `GitHub <https://github.com/kislyuk/watchtower/issues>`_.

License
~~~~~~~
Licensed under the terms of the `Apache License, Version 2.0 <http://www.apache.org/licenses/LICENSE-2.0>`_.

.. image:: https://github.com/kislyuk/watchtower/workflows/Python%20package/badge.svg
        :target: https://github.com/kislyuk/watchtower/actions
.. image:: https://codecov.io/github/kislyuk/watchtower/coverage.svg?branch=master
        :target: https://codecov.io/github/kislyuk/watchtower?branch=master
.. image:: https://img.shields.io/pypi/v/watchtower.svg
        :target: https://pypi.python.org/pypi/watchtower
.. image:: https://img.shields.io/pypi/l/watchtower.svg
        :target: https://pypi.python.org/pypi/watchtower
