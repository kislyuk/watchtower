PyCWL: Python CloudWatch Logging
================================
PyCWL is a log handler for `Amazon Web Services CloudWatch Logs
<https://aws.amazon.com/blogs/aws/cloudwatch-log-service/>`_.

CloudWatch Logs is a log management service built into AWS. It is conceptually similar to services like Splunk and
Loggly, but is more lightweight, cheaper, and tightly integrated with the rest of AWS.

PyCWL, in turn, is a lightweight binding between the `Python logging system
<https://docs.python.org/library/logging.html>`_ and the `boto3 AWS SDK <https://github.com/boto/boto3>`_. It lets you
plug your application logging directly into CloudWatch without the need to install a system-wide log collector. It
aggregates logs into batches to avoid sending an API request per each log message, while guaranteeing a delivery
deadline (60 seconds by default).

Installation
~~~~~~~~~~~~
::
    pip install pycwl

Synopsis
~~~~~~~~
Install `awscli <https://pypi.python.org/pypi/awscli>`_ and set your AWS credentials (run ``aws configure``), then::

    import pycwl, logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.addHandler(pycwl.CloudWatchLogHandler())
    logger.info("Hi")
    logger.info(dict(foo="bar", details={}))

After running the example, you can see the log output in your `AWS console
<https://console.aws.amazon.com/cloudwatch/home>`_.

Example: Flask logging with PyCWL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::
    import pycwl, flask, logging

    logging.basicConfig(level=logging.INFO)
    app = flask.Flask("loggable")
    handler = pycwl.CloudWatchLogHandler()
    app.logger.addHandler(handler)
    logging.getLogger("werkzeug").addHandler(handler)

    @app.route('/')
    def hello_world():
        return 'Hello World!'

    if __name__ == '__main__':
        app.run()

(See also `http://flask.pocoo.org/docs/0.10/errorhandling/ <http://flask.pocoo.org/docs/0.10/errorhandling/>`_.)

Examples: Querying CloudWatch logs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This section is not specific to PyCWL. It demonstrates the use of `awscli <https://pypi.python.org/pypi/awscli>`_ and
`jq <http://stedolan.github.io/jq/>`_ to read and search CloudWatch logs on the command line.

For the Flask example above, you can retrieve your application logs with the following two commands::
    aws logs get-log-events --log-group-name pycwl --log-stream-name loggable | jq '.events[].message'
    aws logs get-log-events --log-group-name pycwl --log-stream-name werkzeug | jq '.events[].message'

Authors
-------
* Andrey Kislyuk

Links
-----
* `Project home page (GitHub) <https://github.com/kislyuk/pycwl>`_
* `Documentation (Read the Docs) <https://pycwl.readthedocs.org/en/latest/>`_
* `Package distribution (PyPI) <https://pypi.python.org/pypi/pycwl>`_
* `Amazon CloudWatch <http://aws.amazon.com/cloudwatch/>`_

Bugs
~~~~
Please report bugs, issues, feature requests, etc. on `GitHub <https://github.com/kislyuk/pycwl/issues>`_.

License
-------
Licensed under the terms of the `Apache License, Version 2.0 <http://www.apache.org/licenses/LICENSE-2.0>`_.

.. image:: https://travis-ci.org/kislyuk/pycwl.svg
        :target: https://travis-ci.org/kislyuk/pycwl
.. image:: https://coveralls.io/repos/kislyuk/pycwl/badge.svg?branch=master
        :target: https://coveralls.io/r/kislyuk/pycwl?branch=master
.. image:: https://pypip.in/version/pycwl/badge.svg
        :target: https://pypi.python.org/pypi/pycwl
.. image:: https://pypip.in/download/pycwl/badge.svg
        :target: https://pypi.python.org/pypi/pycwl
.. image:: https://pypip.in/py_versions/pycwl/badge.svg
        :target: https://pypi.python.org/pypi/pycwl
.. image:: https://readthedocs.org/projects/pycwl/badge/?version=latest
        :target: https://pycwl.readthedocs.org/
