Changes for v3.2.0 (2024-04-19)
===============================

-  Use timeout when waiting for queues to empty at shutdown

Changes for v3.1.0 (2024-03-10)
===============================

-  Avoid crashing flush() when CreateLogStream API call is throttled
   (#192)

-  Replace deprecated function datatime.utcnow() (#196)

Changes for v3.0.1 (2023-01-29)
===============================

-  Truncate messages based on bytes, not unicode characters (#181)

-  Test suite improvements (#180, #182)

Changes for v3.0.0 (2022-01-26)
===============================

-  Use repr to represent all JSON fields of unknown types by default.
   Previously, when passing a mapping (dictionary) as a log message,
   watchtower would replace datetime objects with their “.isoformat()”
   string representation, and would replace all other
   non-JSON-serializable objects with ``null``. The new behavior is to
   use the output of repr() to represent these non-JSON-serializable
   objects. This change may cause your logger to log more data than you
   intended, which is why it triggers a major version bump. If you use
   watchtower to log sensitive information or objects with large repr
   strings, you are advised to examine your log messages to see if any
   newly visible data should be sanitized. If you need to customize this
   behavior, you can pass a custom JSON default serializer using the
   ``json_serialize_default`` keyword argument.

Changes for v2.1.1 (2022-01-07)
===============================

-  Use correct default log stream name

Changes for v2.1.0 (2022-01-07)
===============================

-  Deconflict log streams from process pools in default log stream name

-  Documentation and CI improvements

Changes for v2.0.1 (2021-11-29)
===============================

-  Update empty message filtering to catch formatted string case (#162)

Changes for v2.0.0 (2021-11-13)
===============================

-  Rename log_group to log_group_name for consistency with the Boto3 API

-  Rename stream_name to log_stream_name for consistency with the Boto3
   API

-  Introduce the ability to pass a Boto3 logs client and remove the
   ability to pass Boto3 sessions

-  Document the ability to pass a Boto3 configuration profile name for
   declarative configs

-  Remove the Django customization, which was deprecated and unneeded.
   Django can use watchtower directly via its logging configuration as
   documented in the readme

-  Introduce configurable log formatters. Special thanks to
   @terencehonles for starting this work (#117, #138)

-  Use logging.Handler.handleError to correctly handle errors while
   processing log records (#149)

-  Move stream name determining logic to separate method (#148)

-  Reset internal state on fork to prevent deadlocks in worker threads
   (#139)

-  Drop Python 3.5 support

-  Expand documentation

-  Update test and release infrastructure

Changes for v1.0.6 (2021-01-17)
===============================

-  Catch OperationAbortedException in \_idempotent_create. Fixes #136

Changes for v1.0.5 (2021-01-13)
===============================

-  Don’t crash if nextSequenceToken is missing. Fixes #134

Changes for v1.0.4 (2021-01-01)
===============================

-  Protect against message storms from sending botocore debug logs

Changes for v1.0.3 (2021-01-01)
===============================

-  Apply filter to self instead of forcing log level on shutdown

Changes for v1.0.2 (2020-12-31)
===============================

Force botocore logging level to be INFO or higher on shutdown

Changes for v1.0.1 (2020-12-21)
===============================

-  Add fix/tests for log stream re-creation regression (#131)

Changes for v1.0.0 (2020-10-28)
===============================

-  Fix sequence token cache (#116)

-  Drop compatibility for Python 2 (#109)

-  Fix message truncation for messages above AWS limit (#112)

-  Allow custom endpoint url (#114)

-  Package API is stable

Changes for v0.8.0 (2020-06-28)
===============================

-  Create log streams lazily (#97)

-  Test and package infrastructure improvements

Changes for v0.7.3 (2019-08-27)
===============================

-  Bug fix on log group retention (#80)

Changes for v0.7.2 (2019-08-26)
===============================

Fix another Homebrew-related release failure

Changes for v0.7.1 (2019-08-26)
===============================

-  Re-release 0.7.0 due to Homebrew-related automation failure

Changes for v0.7.0 (2019-08-26)
===============================

-  Add put_retention_policy (#79)

-  Add create_log_stream (#77)

-  Minor test and doc improvements

Changes for v0.6.0 (2019-05-22)
===============================

-  Set creating_log_stream to False when creation fails. (#72)

-  Define all instance attributes before attempting to create boto
   session (#76)

-  Serialize objects with datetimes, and allow custom serializer default
   functions to be used (#73)

Changes for v0.5.5 (2019-01-22)
===============================

-  Add ‘strftime’ parameter to stream_name formatter (#71)

-  Documentation improvements

Changes for v0.5.4 (2018-11-02)
===============================

-  Short-circuit emit if still initializing

Changes for v0.5.3 (2018-04-16)
===============================

-  Fix close twice hang forever bug (#58)

Changes for v0.5.2 (2017-11-09)
===============================

Fix broken formatting in README

Changes for v0.5.1 (2017-11-09)
===============================

Fix JSON message serialization, part 2

Changes for v0.5.0 (2017-11-09)
===============================

Fix JSON message serialization

Changes for v0.4.1 (2017-09-20)
===============================

-  Warn instead of crashing logger on delivery failure

-  Support for django log (#39)

-  Fix for unhashble type error (fixes issue #44) (#45)

Changes for v0.4.0 (2017-08-11)
===============================

-  Do not shut down on flush()

-  Enhancement: boto3 auth profile option (#41)

-  Documentation improvements




Changes for v0.3.3 (2016-09-15)
===============================

-  Release script fix

Changes for v0.3.2 (2016-09-15)
===============================

Fix makefile targets

Changes for v0.3.1 (2016-09-15)
===============================

-  Fix interrupted release
-  Repo housekeeping

Changes for v0.3.0 (2016-09-15)
===============================

-  Add option to avoid CreateLogGroup (#21; thanks to Hong Minhee)

Version 0.2.0 (2016-03-22)
--------------------------
- Allow specifying log stream name (PR #16, #18). Thanks to @mianos, @fangyizhu.

Version 0.1.8 (2016-03-08)
--------------------------
- Fix docs, skip failed release

Version 0.1.6 (2015-12-13)
--------------------------
- Fix docs

Version 0.1.5 (2015-12-13)
--------------------------
- Allow custom boto3 sessions to be passed in for customization of service connection options (PR #15). Thanks to @clifflu.

Version 0.1.4 (2015-11-20)
--------------------------
- Sort batches by timestamp before sending them. Avoids crashes due to out-of-order log streams fed to the logger and rejected by the CWL API (PR #14). Thanks to @haydenth.

Version 0.1.3 (2015-10-04)
--------------------------
- Fix handling of empty queue at deadline timeout (PR #8). Thanks to @ryanmfw.

Version 0.1.2 (2015-09-07)
--------------------------
- Packaging and documentation fixes.
- Bump boto3 version.

Version 0.1.1 (2015-04-29)
--------------------------
- Documentation fixes.

Version 0.1.0 (2015-04-29)
--------------------------
- Initial release.
