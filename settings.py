import logging
import os

import pytz
from dotenv import load_dotenv

load_dotenv(".env")

TZ = os.environ.get("TZ")
tz = pytz.timezone(TZ)
OPENAI_ORG_ID = os.environ.get("OPENAI_ORG_ID")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TELEGRAM_API_KEY = os.environ.get("TELEGRAM_API_KEY")
REQUEST_COOLING_PERIOD_SEC = int(os.environ.get("REQUEST_COOLING_PERIOD_SEC"))
REJECT_COOLING_PERIOD_DAYS = int(os.environ.get("REJECT_COOLING_PERIOD_DAYS"))
ADMIN_ID = os.environ.get("ADMIN_ID")
MODELS = os.environ.get("MODELS").split(',')
LOGGER_MODE = os.environ.get("LOGGER_MODE")
DROP_DATA, = range(1)
WEBHOOKURL = os.environ.get("WEBHOOKURL")
PORT = os.environ.get("PORT")

level = logging.getLevelName(LOGGER_MODE)

LIMITS = {
    'standard': {
        'limit_daily': 20,
        'limit_weekly': 100
    },
    'reduced': {
        'limit_daily': 2,
        'limit_weekly': 5
    },
    'unlimited': {
        'limit_daily': None,
        'limit_weekly': None
    },
    'rejected': {
        'limit_daily': 0,
        'limit_weekly': 0
    }
}