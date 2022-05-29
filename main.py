import logging, os
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
    try:
        with open(config.BOT_TOKEN_FILE, 'r') as token_file:
            token = token_file.read()
    except FileNotFoundError as error:
        print('Bot token file not found.')
        return
    updater = Updater(token)

    # Attach handlers
    dispatcher = updater.dispatcher
    dispatcher.add_handler(start.handler)
    dispatcher.add_handler(help.handler)
    dispatcher.add_handler(book.handler, 0)
    dispatcher.add_handler(change.handler, 1)
    dispatcher.add_handler(check.handler, 2)
    dispatcher.add_handler(mybookings.handler)
    dispatcher.add_handler(admin.handler, 3)

    # Run bot
    port = int(os.environ.get('PORT', 5000))
    updater.start_webhook(
        listen = '0.0.0.0',
        port = port,
        url_path = token
    )
    updater.bot.setWebhook(f'https://facilities-bot.herokuapp.com/{token}')
    updater.idle()

if __name__ == '__main__':
    main()