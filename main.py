import logging
from telegram import Bot, BotCommandScopeChat, ChatAdministratorRights
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
    
    # Create users database if it doesn't exist
    database.create_if_not_exists()

    # Initialise bot and updater
    bot = Bot(config.BOT_TOKEN)
    updater = Updater(config.BOT_TOKEN)

    # Attach handlers
    dispatcher = updater.dispatcher
    dispatcher.add_handler(book.handler, 0)
    dispatcher.add_handler(change.handler, 1)
    dispatcher.add_handler(check.handler, 2)
    dispatcher.add_handler(admin.handler, 3)
    dispatcher.add_handler(mybookings.handler, 4)
    dispatcher.add_handler(help.handler, 5)
    dispatcher.add_handler(start.handler, 6)
        
    # Configure bot commands
    default_commands = config.COMMANDS_BOOKING + config.COMMANDS_SETTING
    admin_commands = config.COMMANDS_ADMIN + default_commands
    bot.set_my_commands(default_commands)
    for admin_uid in config.ADMIN_USERS:
        bot.set_my_commands(admin_commands, scope = BotCommandScopeChat(admin_uid))
    
    # Update admin users
    db_admin_users = database.retrieve_admins()
    for user_id in db_admin_users - config.ADMIN_USERS:
        bot.delete_my_commands(BotCommandScopeChat(user_id))
    for user_id in db_admin_users ^ config.ADMIN_USERS:
        database.toggle_admin(int(user_id))
    
    # Configure default bot admin rights for facilities log channel
    rights = ChatAdministratorRights(
        is_anonymous = False,
        can_manage_chat = False,
        can_delete_messages = False,
        can_manage_video_chats = False,
        can_restrict_members = False,
        can_promote_members = False,
        can_change_info = False,
        can_invite_users = False,
        can_post_messages = True
    )
    bot.set_my_default_administrator_rights(rights, for_channels = True)

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