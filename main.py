import logging
from pathlib import Path
from telegram.ext import Updater, PicklePersistence
from commands import start, help, book, change, check, mybookings, admin
import config, database

# Enable logging
logging.basicConfig(
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level = logging.INFO
)

def main():

    # Create data and keys directories if they don't exist
    project_directory = Path(__file__).parents[0]
    project_directory.joinpath('data').mkdir(exist_ok = True)
    project_directory.joinpath('keys').mkdir(exist_ok = True)

    # Create users database if it doesn't exist
    database.create_if_not_exists()

    # Create bot updater
    updater = Updater(config.BOT_TOKEN)

    # Attach handlers
    dispatcher = updater.dispatcher
    dispatcher.add_handler(start.handler, 6)
    dispatcher.add_handler(help.handler, 5)
    dispatcher.add_handler(book.handler, 0)
    dispatcher.add_handler(change.handler, 1)
    dispatcher.add_handler(check.handler, 2)
    dispatcher.add_handler(mybookings.handler, 4)
    dispatcher.add_handler(admin.handler, 3)

    # Run bot
    updater.start_webhook(
        listen = '0.0.0.0',
        port = int(config.WEBHOOK_PORT),
        url_path = config.BOT_TOKEN,
        webhook_url = f'https://facilities-bot.herokuapp.com/{config.BOT_TOKEN}'
    )
    updater.idle()

if __name__ == '__main__':
    main()