Watchtower: Python CloudWatch Logging
=====================================
Watchtower is a log handler for `Amazon Web Services CloudWatch Logs
<https://aws.amazon.com/blogs/aws/cloudwatch-log-service/>`_.

CloudWatch Logs is a log management service built into AWS. It is conceptually similar to services like Splunk and
Loggly, but is more lightweight, cheaper, and tightly integrated with the rest of AWS.

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

    from boto3.session import Session
    
    AWS_ACCESS_KEY_ID = 'your access key'
    AWS_SECRET_ACCESS_KEY = 'your secret access key'
    AWS_REGION_NAME = 'your region'

    boto3_session = Session(aws_access_key_id=AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                            region_name=AWS_REGION_NAME)

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'root': {
            'level': logging.ERROR,
            'handlers': ['console'],
        },
        'formatters': {
            'simple': {
                'format': u"%(asctime)s [%(levelname)-8s] %(message)s",
                'datefmt': "%Y-%m-%d %H:%M:%S"
            },
            'aws': {
                # you can add specific format for aws here
                'format': u"%(asctime)s [%(levelname)-8s] %(message)s",
                'datefmt': "%Y-%m-%d %H:%M:%S"
            },
        },

        'handlers': {
            'watchtower': {
                'level': 'DEBUG',
                'class': 'watchtower.CloudWatchLogHandler',
                         'boto3_session': boto3_session,
                         'log_group': 'MyLogGroupName',
                         'stream_name': 'MyStreamName',
                'formatter': 'aws',
            },
        }
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
under the stream name ``MyStreamName``. Instead of setting credentials via ``AWS_ACCESS_KEY_ID`` and other variables,
you can also assign an IAM role to your instance and omit those parameters, prompting boto3 to ingest credentials from
instance metadata.

(See also the [Django logging documentation](https://docs.djangoproject.com/en/dev/topics/logging/)).

Examples: Querying CloudWatch logs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This section is not specific to Watchtower. It demonstrates the use of awscli and jq to read and search CloudWatch logs
on the command line.

For the Flask example above, you can retrieve your application logs with the following two commands::

    aws logs get-log-events --log-group-name watchtower --log-stream-name loggable | jq '.events[].message'
    aws logs get-log-events --log-group-name watchtower --log-stream-name werkzeug | jq '.events[].message'

CloudWatch Logs supports alerting and dashboards based on `metric filters
<http://docs.aws.amazon.com/AmazonCloudWatch/latest/DeveloperGuide/FilterAndPatternSyntax.html>`_, which are pattern
rules that extract information from your logs and feed it to alarms and dashboard graphs. The following example shows
logging structured JSON data using Watchtower, setting up a metric filter to extract data from the log stream, a dashboard to
visualize it, and an alarm that sends an email::

    TODO

Examples: Python Logging Config
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python has the ability to provide a configuration file that can be loaded in order to separate the logging
configuration from the code. Historically, Python has used the `logging.config.fileConfig` function to do
so, however, that feature lacks the ability to use keyword args. Python 2.7 introduced a new feature to
handle logging that is more robust - `logging.config.dictConfig` which profiles the ability to do more
advanced Filters, but more importantly adds keyword args, thus allowing the `logging.config` functionality
to instantiate Watchtower.

The following are two example YAML configuration files that can be loaded using `PyYaml`. The resulting
`dict` object can then be loaded into `logging.config.dictConfig`. The first example is a basic example
that relies on the default configuration provided by `boto3`:

.. code-block:: yaml
    # Default AWS Config
    version: 1
    formatters:
        json:
            format: "[%(asctime)s] %(process)d %(levelname)s %(name)s:%(funcName)s:%(lineno)s - %(message)s"
        plaintext:
            format: "[%(asctime)s] %(process)d %(levelname)s %(name)s:%(funcName)s:%(lineno)s - %(message)s"
    handlers:
        console:
            (): logging.StreamHandler
            level: DEBUG
            formatter: plaintext
            stream: sys.stdout
        watchtower:
            formatter: json
            level: DEBUG
            (): watchtower.CloudWatchLogHandler
            log_group: logger
            stream_name:  loggable
            send_interval: 1
            create_log_group: False
    loggers:
        root:
            handlers: [console, watchtower, logfile]
        boto:
            handlers: [console]
        boto3:
            handlers: [console]
        botocore:
            handlers: [console]
        requests:
            handlers: [console]


The above works well if you can use the default configuration, or rely on environmental variables.
However, sometimes one may want to use different credentials for logging than used for other functionality;
in this case the `boto3_profile_name` option to Watchtower can be used to profile a profile name:

.. code-block:: yaml
    # AWS Config Profile
    version: 1
    formatters:
        json:
            format: "[%(asctime)s] %(process)d %(levelname)s %(name)s:%(funcName)s:%(lineno)s - %(message)s"
        plaintext:
            format: "[%(asctime)s] %(process)d %(levelname)s %(name)s:%(funcName)s:%(lineno)s - %(message)s"
    handlers:
        console:
            (): logging.StreamHandler
            level: DEBUG
            formatter: plaintext
            stream: sys.stdout
        watchtower:
            formatter: json
            level: DEBUG
            (): watchtower.CloudWatchLogHandler
            log_group: logger
            stream_name:  loggable
            boto3_profile_name: watchtowerlogger
            send_interval: 1
            create_log_group: False
    loggers:
        root:
            handlers: [console, watchtower, logfile]
        boto:
            handlers: [console]
        boto3:
            handlers: [console]
        botocore:
            handlers: [console]
        requests:
            handlers: [console]

For the more advanced configuration, the following configuration file will profile
the matching credentials to the `watchtowerlogger` profile:

.. code-block:: cfg
    [profile watchtowerlogger]
    aws_access_key_id=MyAwsAccessKey
    aws_secret_access_key=MyAwsSecretAccessKey
    region=us-east-1

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
        with open('logging.yml', 'r') as log_config:
            config_yml = log_config.read()
            config_dict = yaml.load(config_yml)
            logging.config.dictConfig(config_dict)
            app.run()

Authors
-------
* Andrey Kislyuk

Links
-----
* `Project home page (GitHub) <https://github.com/kislyuk/watchtower>`_
* `Documentation (Read the Docs) <https://watchtower.readthedocs.io/en/latest/>`_
* `Package distribution (PyPI) <https://pypi.python.org/pypi/watchtower>`_
* `AWS CLI CloudWatch Logs plugin <https://pypi.python.org/pypi/awscli-cwlogs>`_
* `Docker awslogs adapter <https://github.com/docker/docker/blob/master/daemon/logger/awslogs/cloudwatchlogs.go>`_

Bugs
~~~~
Please report bugs, issues, feature requests, etc. on `GitHub <https://github.com/kislyuk/watchtower/issues>`_.

License
-------
Licensed under the terms of the `Apache License, Version 2.0 <http://www.apache.org/licenses/LICENSE-2.0>`_.

.. image:: https://travis-ci.org/kislyuk/watchtower.svg
        :target: https://travis-ci.org/kislyuk/watchtower
.. image:: https://codecov.io/github/kislyuk/watchtower/coverage.svg?branch=master
        :target: https://codecov.io/github/kislyuk/watchtower?branch=master
.. image:: https://img.shields.io/pypi/v/watchtower.svg
        :target: https://pypi.python.org/pypi/watchtower
.. image:: https://img.shields.io/pypi/l/watchtower.svg
        :target: https://pypi.python.org/pypi/watchtower
.. image:: https://readthedocs.org/projects/watchtower/badge/?version=latest
        :target: https://watchtower.readthedocs.io/
