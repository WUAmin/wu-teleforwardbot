import os
import subprocess
import sys

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


def button_manage_bot(update, context, must_edit=True):
    query = update.callback_query
    keyboard = [[InlineKeyboardButton("Show Contacts", callback_data='show_contacts'),
                 InlineKeyboardButton("Update from git", callback_data='update_git')],
                [InlineKeyboardButton("Restart Bot", callback_data='restart_bot'),
                 InlineKeyboardButton("Stop Bot", callback_data='stop_bot')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if must_edit:
        query.reply_text('Please choose:',
                         reply_markup=reply_markup,
                         parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        update.message.reply_text('Please choose:',
                                  reply_markup=reply_markup,
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def button_stop_bot_confirm(update, context, must_edit=True):
    query = update.callback_query
    keyboard = [[InlineKeyboardButton("Yes", callback_data='stop_bot_yes'),
                 InlineKeyboardButton("No", callback_data='stop_bot_no')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if must_edit:
        query.edit_message_text(
            'Are you sure you want to stop the BOT ?\nIt would need `manually start` from server again.',
            reply_markup=reply_markup,
            parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        update.message.reply_text(
            'Are you sure you want to stop the BOT ?\nIt would need `manually start` from server again.',
            reply_markup=reply_markup,
            parse_mode=telegram.ParseMode.MARKDOWN)


def buttons(update, context):
    auth_level = check_auth(update.effective_chat.id)
    query = update.callback_query
    if query.data == 'show_contacts':
        # run "git pull" on system
        query.edit_message_text(text="There was {} contacts".format(len(settings.contacts)),
                                parse_mode=telegram.ParseMode.MARKDOWN)
        for c in settings.contacts:
            msg = 'Title: *{}*\n'.format(c['title'])
            msg += 'Type: *{}*\n'.format(c['type'])
            msg += 'ID: `{}`\n'.format(c['id'])
            msg += 'Name: *{} {}*\n'.format(c['first_name'], c['last_name'])
            msg += 'Username: *{}*\n'.format(c['username'])
            update.effective_message.reply_text(
                msg, parse_mode=telegram.ParseMode.MARKDOWN)

    elif query.data == 'update_git':
        # run "git pull" on system
        p = os.popen(r'cd "{}";git pull'.format(
            os.path.dirname(os.path.realpath(sys.argv[0]))))
        msg = p.read()
        query.edit_message_text(text="Update from git: ```{}```".format(msg),
                                parse_mode=telegram.ParseMode.MARKDOWN)
    elif query.data == 'restart_bot':
        # run "git pull" on system
        msd_d = query.edit_message_text(
            text="Restarting Bot...", parse_mode=telegram.ParseMode.MARKDOWN)
        p = os.popen(
            r'cd "{}";kill -9 {}; python3 {} --restart={},{}'.format(os.path.dirname(os.path.realpath(sys.argv[0])),
                                                                     os.getpid(), os.path.realpath(
                                                                         sys.argv[0]),
                                                                     msd_d['message_id'],
                                                                     msd_d['chat']['id']))
        msg = p.read()
        query.edit_message_text(text="Restarting Bot: ```{}```".format(msg),
                                parse_mode=telegram.ParseMode.MARKDOWN)
    elif query.data == 'stop_bot':
        button_stop_bot_confirm(update, context, must_edit=True)
    elif query.data == 'stop_bot_yes':
        # run "git pull" on system
        msd_d = query.edit_message_text(
            text="Stopping Bot...", parse_mode=telegram.ParseMode.MARKDOWN)
        p = os.popen(
            r'cd "{}";kill -9 {}'.format(os.path.dirname(os.path.realpath(sys.argv[0])), os.getpid()))
        msg = p.read()
        query.edit_message_text(text="Stpping bot Bot: ```{}```".format(
            msg), parse_mode=telegram.ParseMode.MARKDOWN)
    elif query.data == 'stop_bot_no':
        query.edit_message_text(
            text="Good!", parse_mode=telegram.ParseMode.MARKDOWN)
    elif query.data == 'my_chat_id':
        query.edit_message_text(text="Your User ID: `{}`\nLevel: *{}*".format(update.effective_chat.id,
                                                                              auth_level.name),
                                parse_mode=telegram.ParseMode.MARKDOWN)


def cmd_start(update, context):
    try:
        auth_level = check_auth(update.effective_chat.id)
        # ------------ ADMIN_LEVEL -------------
        if auth_level.value >= AuthLevel.ADMIN.value:
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="{}x Hello".format(auth_level))
        # ------------- MOD_LEVEL --------------
        elif auth_level.value >= AuthLevel.MOD.value:
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="{}x Hello".format(auth_level))
        # ------------ USERS_LEVEL -------------
        # --------- UNAUTHORIZED_LEVEL ---------
        # --------------------------------------
    except Exception as e:
        print("Error: %s" % str(e))


def cmd_id(update, context):
    try:
        auth_level = check_auth(update.effective_chat.id)
        # ------------ ADMIN_LEVEL -------------
        # ------------- MOD_LEVEL --------------
        if auth_level.value >= AuthLevel.MOD.value:
            keyboard = [[InlineKeyboardButton("My Chat ID", callback_data='my_chat_id'),
                         InlineKeyboardButton("Next Message Chat ID", callback_data='next_chat_id')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                'Please choose:', reply_markup=reply_markup)
        # ------------ USERS_LEVEL -------------
        # --------- UNAUTHORIZED_LEVEL ---------
        # --------------------------------------
    except Exception as e:
        print("Error: %s" % str(e))


def manage_bot(update, context):
    try:
        auth_level = check_auth(update.effective_chat.id)
        # ------------ ADMIN_LEVEL -------------
        if auth_level.value >= AuthLevel.ADMIN.value:
            button_manage_bot(update, context, must_edit=False)
        # ------------- MOD_LEVEL --------------
        # ------------ USERS_LEVEL -------------
        # --------- UNAUTHORIZED_LEVEL ---------
        # --------------------------------------
    except Exception as e:
        print("Error: %s" % str(e))


def all_msg(update, context):
    try:
        auth_level = check_auth(update.effective_chat.id)
        log_update_simple(update)
        # ------------ ADMIN_LEVEL -------------
        if auth_level.value >= AuthLevel.ADMIN.value:
            pass
        # ------------- MOD_LEVEL --------------
        # ------------ USERS_LEVEL -------------
        # --------- UNAUTHORIZED_LEVEL ---------
        # --------------------------------------

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
            settings.save_json_settings(os.path.join(
                os.path.dirname(sys.argv[0]), 'settings.json'))

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


def main():
    settings.load_json_settings(os.path.join(
        os.path.dirname(sys.argv[0]), 'settings.json'))
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

    # Register Manage Bot
    manage_bot_handler = CommandHandler('managebot', manage_bot)
    dispatcher.add_handler(manage_bot_handler)

    # Register inline buttons
    dispatcher.add_handler(CallbackQueryHandler(buttons))

    # Register all messages
    # textmsg_handler = MessageHandler(Filters.text, textmsg, message_updates=True, channel_post_updates=False)
    # dispatcher.add_handler(textmsg_handler)

    # Register all messages
    allmsg_handler = MessageHandler(
        Filters.all, all_msg, message_updates=True, channel_post_updates=True)
    dispatcher.add_handler(allmsg_handler)

    # parse arguments
    for arg in sys.argv:
        try:
            if arg.startswith('--restart='):
                mid, cid = arg.split('=')[1].split(',')
                updater.bot.edit_message_text(chat_id=cid,
                                              message_id=mid,
                                              text="Bot Restarted",
                                              parse_mode=telegram.ParseMode.MARKDOWN)
                break
        except Exception as e:
            print("Error: %s" % str(e))

    # Start BOT
    updater.start_polling()


main()

# p = os.popen(r'whereis git', cwd=os.path.dirname(os.path.realpath(sys.argv[0])))

# cmd = r'echo "HI";cd "{}";kill -9 {}; python3 {}'.format(
#     os.path.dirname(os.path.realpath(sys.argv[0])), os.getpid(), os.path.realpath(sys.argv[0]))
# p = os.popen(cmd)
# msg = p.read()
# print(msg)
