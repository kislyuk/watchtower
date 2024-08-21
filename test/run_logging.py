import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from watchtower import CloudWatchLogHandler  # noqa: E402

handler = CloudWatchLogHandler(log_stream_name="run_logging")
logger = logging.getLogger("run_logging")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.info("msg")
handler.close()
