Version 0.1.7 (2016-04-08)
--------------------------
- Fix docs, part 2

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
