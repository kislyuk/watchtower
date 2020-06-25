import logging

from watchtower import CloudWatchLogHandler

handler = CloudWatchLogHandler(stream_name='run_logging')
logger = logging.getLogger('run_logging')
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.info('msg')
handler.close()
