import logging
from pathlib import Path
from telegram import Bot, BotCommandScopeChat
from telegram.ext import Updater
from commands import start, help, book, change, check, mybookings, admin
from utilities import database
import config

# Enable logging
logging.basicConfig(
    format = '[%(levelname)s/%(name)s] %(message)s', 
    level = logging.INFO
)

def main():

    # Create data and keys directories if they don't exist
    project_directory = Path(__file__).parents[0]
    project_directory.joinpath('data').mkdir(exist_ok = True)
    project_directory.joinpath('keys').mkdir(exist_ok = True)

    # Create users database if it doesn't exist
    database.create_if_not_exists()

    # Initialise bot and updater
    bot = Bot(config.BOT_TOKEN)
    updater = Updater(bot=bot)

    # Attach handlers
    dispatcher = updater.dispatcher
    dispatcher.add_handler(start.handler, 6)
    dispatcher.add_handler(help.handler, 5)
    dispatcher.add_handler(book.handler, 0)
    dispatcher.add_handler(change.handler, 1)
    dispatcher.add_handler(check.handler, 2)
    dispatcher.add_handler(mybookings.handler, 4)
    dispatcher.add_handler(admin.handler, 3)
    
    # Add bot commands
    bot.set_my_commands(config.COMMANDS_DEFAULT)
    for admin_uid in config.ADMIN_UID_LIST:
        bot.set_my_commands(
            commands = config.COMMANDS_ADMIN + config.COMMANDS_DEFAULT,
            scope = BotCommandScopeChat(admin_uid)
        )

    # Run bot
    updater.start_webhook(
        listen = '0.0.0.0',
        port = int(config.WEBHOOK_PORT),
        url_path = config.BOT_TOKEN,
        webhook_url = f'{config.HEROKU_APP_URL}{config.BOT_TOKEN}'
    )
    updater.idle()

if __name__ == '__main__':
    main()
