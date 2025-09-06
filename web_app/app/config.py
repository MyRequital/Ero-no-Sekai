from _configs.config import BASE_DIR
import os
from _configs.log_config import logger



class Config:
    DEBUG = True
    JSONIFY_PRETTYPRINT_REGULAR = True
    TEMPLATES_PATH = os.path.join(BASE_DIR, 'web_app', 'templates')

