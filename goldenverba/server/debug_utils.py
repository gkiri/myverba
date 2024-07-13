# debug_utils.py

import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('verba_debug')

# Get debug flag from environment variable
DEBUG = os.getenv('VERBA_DEBUG', 'False').lower() in ('true', '1', 't')

def debug_log(*args):
    """Log debug messages if DEBUG is True."""
    if DEBUG:
        logger.debug(' '.join(map(str, args)))

def info_log(*args):
    """Log info messages."""
    logger.info(' '.join(map(str, args)))

def warn_log(*args):
    """Log warning messages."""
    logger.warning(' '.join(map(str, args)))

def error_log(*args):
    """Log error messages."""
    logger.error(' '.join(map(str, args)))