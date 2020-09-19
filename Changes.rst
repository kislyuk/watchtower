UNRELEASED
==========

- Drop support for Python 2

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
