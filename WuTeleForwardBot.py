import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
import telegram  # https://github.com/python-telegram-bot/python-telegram-bot
import settings as settings
from settings import AuthLevel
import logging


def check_auth(chat_id):
    if chat_id in settings.chat_ids['admins']:
        return AuthLevel.ADMIN
    elif chat_id in settings.chat_ids['groups']:
        return AuthLevel.MOD
    elif chat_id in settings.chat_ids['users']:
        return AuthLevel.USER
    else:
        return AuthLevel.UNAUTHORIZED


def add_filename_to_media(update):
    # if update.effective_message.
    print(update)


def log_update_simple(update):
    logging.info("Title: {} | Username: {} | ID: {} | Date: {} | Text: {}".format(
        update.effective_message.chat.title,
        update.effective_message.chat.username,
        update.effective_chat.id,
        update.effective_message.date,
        update.effective_message.text))


def cmd_start(update, context):
    try:
        auth_level = check_auth(update.effective_chat.id)
        # ------------ ADMIN_LEVEL -------------
        if auth_level.value >= AuthLevel.ADMIN.value:
            context.bot.send_message(chat_id=update.effective_chat.id, text="{}x Hello".format(auth_level))
        # ------------ MOD_LEVEL ------------
        elif auth_level.value >= AuthLevel.MOD.value:
            context.bot.send_message(chat_id=update.effective_chat.id, text="{}x Hello".format(auth_level))
        # ------------ USERS_LEVEL -------------
        elif auth_level.value >= AuthLevel.USER.value:
            context.bot.send_message(chat_id=update.effective_chat.id, text="{}x Hello".format(auth_level))
        # --------- UNAUTHORIZED_LEVEL ---------
    except Exception as e:
        print("Error: %s" % str(e))


def cmd_id_button(update, context):
    auth_level = check_auth(update.effective_chat.id)
    query = update.callback_query
    if query.data == 'mychatid':
        query.edit_message_text(
            text="Your User ID: `{}`\nLevel: *{}*".format(update.effective_chat.id, auth_level.name),
            parse_mode=telegram.ParseMode.MARKDOWN)


def cmd_id(update, context):
    try:
        msg = "Your User ID: `{}`".format(update.message.chat_id, update.message.message_id)
        auth_level = check_auth(update.effective_chat.id)
        # ------------ ADMIN_LEVEL -------------
        # ------------ MOD_LEVEL ------------
        if auth_level.value >= AuthLevel.MOD.value:
            keyboard = [[InlineKeyboardButton("My Chat ID", callback_data='mychatid'),
                         InlineKeyboardButton("Next Message Chat ID", callback_data='nextchatid')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text('Please choose:', reply_markup=reply_markup)
        # ------------ USERS_LEVEL -------------
        # elif auth_level.value >= AuthLevel.USER.value:
        #     msg += "\nLevel: *{}*".format(auth_level.name)
        #     pass
        # --------- UNAUTHORIZED_LEVEL ---------
        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     reply_to_message_id=update.message.message_id,
                                     text="Your User ID: `{}`".format(update.message.chat_id,
                                                                      update.message.message_id),
                                     parse_mode=telegram.ParseMode.MARKDOWN)
    except Exception as e:
        print("Error: %s" % str(e))


def all_msg(update, context):
    try:
        auth_level = check_auth(update.effective_chat.id)
        log_update_simple(update)
        # ------------ ADMIN_LEVEL -------------
        if auth_level.value >= AuthLevel.ADMIN.value:
            # context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id,
            #                          text="Your User ID: `{}`\nYour Message ID: `{}`"
            #                          .format(update.message.chat_id, update.message.message_id),
            #                          parse_mode=telegram.ParseMode.MARKDOWN)
            pass
        # ------------ MOD_LEVEL ------------
        elif auth_level.value >= AuthLevel.MOD.value:
            # if update.effective_chat.id == settings.settings.WuMedia2_ID:
            #     add_filename_to_media(update)
            pass
        # ------------ USERS_LEVEL -------------
        # --------- UNAUTHORIZED_LEVEL ---------

        # Search for new contacts
        found_contact = False
        for cont in settings.contacts:
            if cont['id'] == update.effective_chat.id:
                found_contact = True
                break
        if not found_contact:
            settings.contacts.append({
                "id": update.effective_chat.id,
                "type": update.effective_chat.type,
                "title": update.effective_chat.title,
                "first_name": update.effective_chat.first_name,
                "last_name": update.effective_chat.last_name,
                "username": update.effective_chat.username,
            })
            settings.save_json_settings(os.path.join(os.path.dirname(__file__), 'settings.json'))

        # check forward rules on this msg
        for fr in settings.forward_rules:
            if fr['from'] == update.effective_chat.id:
                for kw in fr['keywords']:
                    if kw == "*" or kw in update.effective_message.text:
                        context.bot.forward_message(chat_id=fr['to'],
                                                    from_chat_id=update.effective_message.chat_id,
                                                    message_id=update.effective_message.message_id)
                        break


    except Exception as e:
        print("Error: %s" % str(e))


# def test_conv(update, context):
#     print(update)
def add_group(update, context):
    for member in update.message.new_chat_members:
        update.message.reply_text("{username} add group".format(username=member.username))


def init():
    settings.load_json_settings(os.path.join(os.path.dirname(__file__), 'settings.json'))
    updater = Updater(token=settings.api_token, use_context=True)
    dispatcher = updater.dispatcher

    # Setup Log
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.WARNING)
    # level = logging.INFO)

    # Register /start
    cmd_start_handler = CommandHandler('start', cmd_start)
    dispatcher.add_handler(cmd_start_handler)

    # Register /start
    cmd_id_handler = CommandHandler('id', cmd_id)
    dispatcher.add_handler(cmd_id_handler)
    dispatcher.add_handler(CallbackQueryHandler(cmd_id_button))

    # Register all messages
    # textmsg_handler = MessageHandler(Filters.text, textmsg, message_updates=True, channel_post_updates=False)
    # dispatcher.add_handler(textmsg_handler)

    # Register all messages
    allmsg_handler = MessageHandler(Filters.all, all_msg, message_updates=True, channel_post_updates=True)
    dispatcher.add_handler(allmsg_handler)

    add_group_handle = MessageHandler(Filters.status_update.new_chat_members, add_group)
    dispatcher.add_handler(add_group_handle)

    # Start BOT
    updater.start_polling()


init()
