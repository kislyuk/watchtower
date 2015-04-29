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
------------
::

    pip install pycwl

Synopsis
--------
Install `awscli <https://pypi.python.org/pypi/awscli>`_ and run `aws configure`, then::

    import logging, pycwl
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.addHandler(pycwl.CloudWatchLogHandler())
    logger.info("Hi")

After running the example, you can see the log output in your `AWS console
<https://console.aws.amazon.com/cloudwatch/home>`_.

Example: Flask logging with PyCWL
---------------------------------
::
    TODO

Reading and searching logs on the command line
----------------------------------------------
Install `awscli <https://pypi.python.org/pypi/awscli>`_ and `jq <http://stedolan.github.io/jq/>`_.
::

    aws logs get-log-events --log-group-name pycwl --log-stream-name LOGGER_NAME | jq '.events[].message'

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
