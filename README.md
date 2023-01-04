# Facilities-Bot
Telegram bot for managing facility bookings

## Features
- Make / change / delete bookings
- Deconflict bookings automatically
    - Offers to book alternate facilities
    - Offers to move users' own existing bookings
    - Directs users to contact POCs of existing bookings
- View all bookings on Google Calendar
- Optionally log new / updated bookings in a Telegram channel

## Limitations
- Does not support multiple timezones
- Designed for SAF battalions; some syntax reflects this (e.g. 'rank and name', 'companies')

## Setup
1. [Create a Telegram bot](https://core.telegram.org/bots#creating-a-new-bot) with @BotFather
    - Customise bot description, profile picture, etc. as desired
    - Optionally [create a public Telegram channel](https://telegram.org/faq_channels) and add the bot as an administrator with broadcast rights
2. Create a [Google service account](https://cloud.google.com/iam/docs/service-accounts)
    - [Enable Google Calendar API](https://support.google.com/googleapi/answer/6158841?hl=en) on Google Cloud Console
    - Give the service account ['Make changes to events' permissions](https://support.google.com/calendar/answer/37082) in a Google Calendar
3. [INSERT INSTRUCTIONS FOR RAILWAY.APP DEPLOY].
