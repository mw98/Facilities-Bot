# Facilities-Bot
Telegram bot for managing facility bookings

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## Features
- Book facilities
- Change / delete existing bookings
- Deconflict bookings automatically
    - Offers to book alternate facilities
    - Offers to move users' previous bookings
    - Directs users to contact POCs of existing bookings
- Admins can make bookings as any user
- Bookings are colour coded by user group on Google Calendar
- Optionally record bookings in a separate Telegram channel

## Limitations
- Hardcoded SG timezone (UTC+8)
- Designed for use by SAF battalions; some syntax reflects this (e.g. 'rank and name', 'companies')

## Setup
1. [Create a Telegram bot](https://core.telegram.org/bots#creating-a-new-bot) with @BotFather
    - Customise bot description, profile picture, etc. as desired
2. Create a [Google service account](https://cloud.google.com/iam/docs/service-accounts)
    - [Enable Google Calendar API](https://support.google.com/googleapi/answer/6158841?hl=en) on Google Cloud Console
    - Give the service account ['Make changes to events' permissions](https://support.google.com/calendar/answer/37082) in a Google Calendar
3. Deploy to Heroku
    - Fill in the specified environmental variables as directed
    - If using a free account, [verify the account](https://devcenter.heroku.com/articles/account-verification) and schedule the following job on [Heroku Scheduler](https://devcenter.heroku.com/articles/scheduler#scheduling-jobs) at a 10min interval: `curl https://YOUR-APP-NAME.herokuapp.com`