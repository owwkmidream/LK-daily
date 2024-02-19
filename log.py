import logging
import sys

from config import Config

config = Config()

debug_level = config.get('debug_level')
logging.basicConfig(level=logging.INFO if not debug_level else logging.DEBUG,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s - %(message)s',
                    stream=sys.stdout)
