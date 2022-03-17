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
<https://console.aws.amazon.com/cloudwatch/home>`_ under the **watchtower** log group.

IAM permissions
~~~~~~~~~~~~~~~
The process running watchtower needs to have access to IAM credentials to call the CloudWatch Logs API. The standard
procedure for loading and configuring credentials is described in the
`Boto3 Credentials documentation <https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html>`_.
When running Watchtower on an EC2 instance or other AWS compute resource, boto3 automatically loads credentials from
`instance metadata <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html>`_ (IMDS) or
container credentials provider (AWS_WEB_IDENTITY_TOKEN_FILE or AWS_CONTAINER_CREDENTIALS_FULL_URI). The easiest way to
grant the right permissions to the IAM role associated with these credentials is by attaching an AWS
`managed IAM policy <https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_managed-vs-inline.html>`_ to the
role. While AWS provides no generic managed CloudWatch Logs writer policy, we recommend that you use the
``arn:aws:iam::aws:policy/AWSOpsWorksCloudWatchLogs`` managed policy, which has just the right permissions without being
overly broad.

Example: Flask logging with Watchtower
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the following configuration to send Flask logs to a CloudWatch Logs stream called "loggable":

.. code-block:: python

    import watchtower, flask, logging

    logging.basicConfig(level=logging.INFO)
    app = flask.Flask("loggable")
    handler = watchtower.CloudWatchLogHandler(log_group_name=app.name)
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

    AWS_REGION_NAME = "us-west-2"

    boto3_logs_client = boto3.client("logs", region_name=AWS_REGION_NAME)

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'root': {
            'level': 'DEBUG',
            # Adding the watchtower handler here causes all loggers in the project that
            # have propagate=True (the default) to send messages to watchtower. If you
            # wish to send only from specific loggers instead, remove "watchtower" here
            # and configure individual loggers below.
            'handlers': ['watchtower', 'console'],
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
            'watchtower': {
                'class': 'watchtower.CloudWatchLogHandler',
                'boto3_client': boto3_logs_client,
                'log_group_name': 'YOUR_DJANGO_PROJECT_NAME',
                # Decrease the verbosity level here to send only those logs to watchtower,
                # but still see more verbose logs in the console. See the watchtower
                # documentation for other parameters that can be set here.
                'level': 'DEBUG'
            }
        },
        'loggers': {
            # In the debug server (`manage.py runserver`), several Django system loggers cause
            # deadlocks when using threading in the logging handler, and are not supported by
            # watchtower. This limitation does not apply when running on production WSGI servers
            # (gunicorn, uwsgi, etc.), so we recommend that you set `propagate=True` below in your
            # production-specific Django settings file to receive Django system logs in CloudWatch.
            'django': {
                'level': 'DEBUG',
                'handlers': ['console'],
                'propagate': False
            }
            # Add any other logger-specific configuration here.
        }
    }

Using this configuration, logs from Django will be sent to Cloudwatch in the log group ``YOUR_DJANGO_PROJECT_NAME``.
To supply AWS credentials to this configuration in development, set your 
`AWS CLI profile settings <https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html>`_ with
``aws configure``. To supply credentials in production or when running on an EC2 instance,
assign an IAM role to your instance, which will cause boto3 to automatically ingest IAM role credentials from
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
these features on the command line, the author of Watchtower has published an open source CLI toolkit called
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

Log stream naming
~~~~~~~~~~~~~~~~~
For high volume logging applications that utilize process pools, it is recommended that you keep the default log stream
name (``{machine_name}/{program_name}/{logger_name}/{process_id}``) or otherwise make it unique per source using a
combination of these template variables. Because logs must be submitted sequentially to each log stream, independent
processes sending logs to the same log stream will encounter sequence token synchronization errors and spend extra resources
automatically recovering from them. As the number of processes increases, this overhead will grow until logs fail to
deliver and get dropped (causing a warning on stderr). Partitioning logs into streams by source avoids this contention.

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

AWS Lambda
~~~~~~~~~~
Watchtower is not suitable or necessary for applications running on AWS Lambda. All AWS Lambda logs (i.e. all lines
printed to stderr by the runtime in the Lambda) are automatically sent to CloudWatch Logs, into
`log groups under the /aws/lambda/ prefix <https://console.aws.amazon.com/cloudwatch/home?#logsV2:log-groups$3FlogGroupNameFilter$3D$252Faws$252Flambda>`_.

AWS Lambda `suspends (freezes) all processes in its execution environment <https://docs.aws.amazon.com/lambda/latest/dg/runtimes-context.html>`_
once the invocation is complete and until the next invocation, if any. This means any asynchronous background
processes and threads, including watchtower, will be suspended and inoperable, so watchtower cannot function
correctly in this execution model.

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
