import os
from datetime import timezone, timedelta
import ujson

# HEROKU
HEROKU_APP_URL = os.environ['HEROKU_APP_URL']
DATABASE_URL = os.environ['DATABASE_URL']

# TELEGRAM
BOT_TOKEN = os.environ['BOT_TOKEN']
ADMIN_USERS = set(ujson.loads(os.getenv('ADMIN_USERS') or '[]'))
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')
CHANNEL_MUTED = (os.getenv('CHANNEL_MUTED') == 'True')
COMMANDS_BOOKING = list(ujson.loads(os.getenv('COMMANDS_BOOKING') or '{}').items())
COMMANDS_SETTING = list(ujson.loads(os.getenv('COMMANDS_SETTING') or '{}').items())
COMMANDS_ADMIN = list(ujson.loads(os.getenv('COMMANDS_ADMIN') or '{}').items())
WEBHOOK_PORT = os.getenv('PORT') or 8443

# GOOGLE CALENDAR
CALENDAR_ID = os.environ['CALENDAR_ID']
CALENDAR_URL = os.getenv('CALENDAR_URL')
SERVICE_ACCOUNT_INFO = ujson.loads(os.environ['SERVICE_ACCOUNT_INFO'])

# BOOKING PARAMETERS
COMPANIES = ujson.loads(os.environ['COMPANIES'])
FACILITIES = ujson.loads(os.os.environ['FACILITIES'])
ALT_FACILITIES = ujson.loads(os.getenv('ALT_FACILITIES') or '{}')
TIMEZONE = timezone(timedelta(hours=8)) # UTC+8