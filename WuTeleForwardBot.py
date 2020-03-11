import json
import logging
import os
import sys
import uuid

import telegram  # https://github.com/python-telegram-bot/python-telegram-bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler

import settings as settings
from settings import AuthLevel


NF_GETSOURCEID_TYPE, NF_GETSOURCEID_FORWARD, NF_GETSOURCEID_ID, NF_GETDESTINATION_TYPE, NF_GETDESTINATION_FORWARD, NF_GETDESTINATION_ID, NF_GETKEYWORDS, NF_VERIFY = range(
    8)
# Setup Log
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


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
    logger.info("Title: {} | Username: {} | ID: {} | Date: {} | Text: {}".format(
        update.effective_message.chat.title,
        update.effective_message.chat.username,
        update.effective_chat.id,
        update.effective_message.date,
        update.effective_message.text))


def button_manage_bot(update, context, must_edit=True):
    query = update.callback_query
    keyboard = [[InlineKeyboardButton("Show Contacts", callback_data='show_contacts'),
                 InlineKeyboardButton("Show Rules", callback_data='show_rules')],
                [InlineKeyboardButton("Backup", callback_data='backup'),
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
    if query.data == 'backup':
        # Send backup as reply
        try:
            query.edit_message_text(text="Sending backup...".format(len(settings.contacts)),
                                    parse_mode=telegram.ParseMode.MARKDOWN)
            context.bot.send_document(chat_id=update.effective_chat.id,
                                      document=open(os.path.join(os.path.dirname(sys.argv[0]), 'settings.json'), 'rb'),
                                      reply_to_message_id=update.effective_message.message_id)
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Error: {}".format(str(e)),
                                     reply_to_message_id=update.effective_message.message_id)
    if query.data == 'show_contacts':
        # Show Contacts
        try:
            query.edit_message_text(text="There was {} contacts".format(len(settings.contacts)),
                                    parse_mode=telegram.ParseMode.MARKDOWN)
            for c in settings.contacts:
                msg = 'Title: *{}*\n'.format(c['title'])
                msg += 'Type: *{}*\n'.format(c['type'])
                msg += 'ID: `{}`\n'.format(c['id'])
                msg += 'Name: *{} {}*\n'.format(c['first_name'], c['last_name'])
                msg += 'Username: *{}*\n'.format(c['username'])
                update.effective_message.reply_text(msg, parse_mode=telegram.ParseMode.MARKDOWN)
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Error: {}".format(str(e)),
                                     reply_to_message_id=update.effective_message.message_id)
    if query.data == 'show_rules':
        # Show Rules
        try:
            query.edit_message_text(text="There was {} rules".format(len(settings.forward_rules)),
                                    parse_mode=telegram.ParseMode.MARKDOWN)
            for r in settings.forward_rules:
                keyboard = [[InlineKeyboardButton("Detail", callback_data=f"detail_rule_{r['uuid']}")],
                            [InlineKeyboardButton("Delete", callback_data=f"delete_rule_{r['uuid']}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.effective_message.reply_text(
                    f"*{r['from']['title']}* `->` *{r['to']['title']}*\n{'|'.join(r['keywords'])}",
                    reply_to_message_id=update.effective_message.message_id,
                    reply_markup=reply_markup,
                    parse_mode=telegram.ParseMode.MARKDOWN)
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Error: {}".format(str(e)),
                                     reply_to_message_id=update.effective_message.message_id)
    if query.data.startswith('delete_rule_'):
        # Delete Rules
        try:
            r_uuid = query.data[12:]
            # query.edit_message_text(text="Deleting rule".format(len(settings.forward_rules)),
            #                         parse_mode=telegram.ParseMode.MARKDOWN)
            for r in settings.forward_rules:
                if r['uuid'] == r_uuid:
                    query.edit_message_text(
                        f"*{r['from']['title']}* `->` *{r['to']['title']}*\n{'|'.join(r['keywords'])}\n\n🗑 Deleted.",
                        reply_to_message_id=update.effective_message.message_id,
                        parse_mode=telegram.ParseMode.MARKDOWN)
                    settings.forward_rules.remove(r)
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Error: {}".format(str(e)),
                                     reply_to_message_id=update.effective_message.message_id)
    if query.data.startswith('detail_rule_'):
        # Detail Rules
        try:
            r_uuid = query.data[12:]
            # query.edit_message_text(text="Deleting rule".format(len(settings.forward_rules)),
            #                         parse_mode=telegram.ParseMode.MARKDOWN)
            for r in settings.forward_rules:
                if r['uuid'] == r_uuid:
                    query.edit_message_text(
                        f"*{r['from']['title']}* `->` *{r['to']['title']}*\n{'|'.join(r['keywords'])}\n\n```{json.dumps(r, indent=2, sort_keys=True)}```",
                        reply_to_message_id=update.effective_message.message_id,
                        parse_mode=telegram.ParseMode.MARKDOWN)
                    break
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Error: {}".format(str(e)),
                                     reply_to_message_id=update.effective_message.message_id)
    elif query.data == 'update_git':
        # Update bot from git
        try:
            p = os.popen(r'cd "{}";git pull'.format(
                os.path.dirname(os.path.realpath(sys.argv[0]))))
            msg = p.read()
            query.edit_message_text(text="Update from git: ```{}```".format(msg),
                                    parse_mode=telegram.ParseMode.MARKDOWN)
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Error: {}".format(str(e)),
                                     reply_to_message_id=update.effective_message.message_id)
    elif query.data == 'restart_bot':
        # Restart Bot
        try:
            msd_d = query.edit_message_text(
                text="Restarting Bot...", parse_mode=telegram.ParseMode.MARKDOWN)
            p = os.popen(
                r'cd "{}";kill -9 {}; python3 {} --restart={},{}'.format(os.path.dirname(os.path.realpath(sys.argv[0])),
                                                                         os.getpid(), os.path.realpath(sys.argv[0]),
                                                                         msd_d['message_id'], msd_d['chat']['id']))
            msg = p.read()
            query.edit_message_text(text="Restarting Bot: ```{}```".format(msg),
                                    parse_mode=telegram.ParseMode.MARKDOWN)
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Error: {}".format(str(e)),
                                     reply_to_message_id=update.effective_message.message_id)
    elif query.data == 'stop_bot':
        # Stop bot
        button_stop_bot_confirm(update, context, must_edit=True)
    elif query.data == 'stop_bot_yes':
        # Yes to stop bot
        try:
            query.edit_message_text(
                text="Stopping Bot...", parse_mode=telegram.ParseMode.MARKDOWN)
            p = os.popen(
                r'cd "{}";kill -9 {}'.format(os.path.dirname(os.path.realpath(sys.argv[0])), os.getpid()))
            msg = p.read()
            query.edit_message_text(text="Stpping bot Bot: ```{}```".format(
                msg), parse_mode=telegram.ParseMode.MARKDOWN)
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Error: {}".format(str(e)),
                                     reply_to_message_id=update.effective_message.message_id)
    elif query.data == 'stop_bot_no':
        # No to stop bot
        query.edit_message_text(text="Good!", parse_mode=telegram.ParseMode.MARKDOWN)
    elif query.data == 'my_chat_id':
        # Show chat id
        query.edit_message_text(
            text="Your User ID: `{}`\nLevel: *{}*".format(update.effective_chat.id, auth_level.name),
            parse_mode=telegram.ParseMode.MARKDOWN)


def newforward_start(update, context):
    try:
        reply_keyboard = [['Forward from Channel'], ['Enter ID/Username']]
        update.message.reply_text('To add new *ForwardRule*, follow these steps:\n'
                                  '1. Add this *Bot* to *source* channel or group as *ADMINISTRATOR*.\n'
                                  '2. Add this *Bot* to *destination* channel or group as *ADMINISTRATOR*.\n'
                                  '3. Enter *source* Channel/Group chat id here or Forward a message from '
                                  '*source* *CHANNEL* here. (No forward from group)\n'
                                  '4. Enter your keywords\n'
                                  '3. Enter *destination* Channel/Group chat id here or Forward a message from '
                                  '*destination* *CHANNEL* here. (No forward from group)\n'
                                  '\nTo cancel this process, use /cancel'
                                  '\n\n_For groups, you can always temporary make them public, enter username of group.'
                                  'then make it private again. This way you can also get group chat id_',
                                  parse_mode=telegram.ParseMode.MARKDOWN,
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return NF_GETSOURCEID_TYPE
    except Exception as e:
        logger.error(str(e))
        update.message.reply_text("Follow the instructions and try again!\n```{}```".format(str(e)),
                                  parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def newforward_get_source_id_type(update, context):
    logger.info("Input type: %s", update.message.text)
    if update.message.text == 'Forward from Channel':
        update.message.reply_text(f'*{update.message.text}*\n'
                                  'Forward message from *source* channel.\n'
                                  '(this method is not working with groups)\n'
                                  '\nTo cancel this process, use /cancel',
                                  parse_mode=telegram.ParseMode.MARKDOWN,
                                  reply_markup=ReplyKeyboardRemove())
        return NF_GETSOURCEID_FORWARD
    elif update.message.text == 'Enter ID/Username':
        update.message.reply_text(f'*{update.message.text}*\n'
                                  'Enter id/username of  *source* channel/group:',
                                  parse_mode=telegram.ParseMode.MARKDOWN,
                                  reply_markup=ReplyKeyboardRemove())
        return NF_GETSOURCEID_ID
    else:
        reply_keyboard = [['Forward from Channel'], ['Enter ID/Username']]
        update.message.reply_text('Try again!',
                                  parse_mode=telegram.ParseMode.MARKDOWN,
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return NF_GETSOURCEID_TYPE


def newforward_get_source_forward(update, context):
    try:
        auth_level = check_auth(update.effective_chat.id)
        # ------------ ADMIN_LEVEL -------------
        # ------------- MOD_LEVEL --------------
        if auth_level.value >= AuthLevel.MOD.value:
            if update.message.forward_from_chat:
                # Preparing message
                txt = 'Source:\n' \
                      f' ℹ️ ID: `{update.message.forward_from_chat.id}`\n'
                if update.message.forward_from_chat.type:
                    txt += f' ℹ️ Type: {update.message.forward_from_chat.type}\n'
                if update.message.forward_from_chat.title:
                    txt += f' ℹ️ Title: *{update.message.forward_from_chat.title}*\n'
                if update.message.forward_from_chat.username:
                    txt += f' ℹ️ Username: `{update.message.forward_from_chat.username}`\n'
                logger.info(txt)
                update.message.reply_text(txt, parse_mode=telegram.ParseMode.MARKDOWN,
                                          reply_markup=ReplyKeyboardRemove())
                update.message.reply_text(
                    'Enter keywords, separate them with comma (,). Use \* for forward everything\n'
                    'Example:\n   books,#music'
                    '\nTo cancel this process, use /cancel',
                    parse_mode=telegram.ParseMode.MARKDOWN,
                    reply_markup=ReplyKeyboardRemove())
                settings.new_rule['from'] = {
                    'id': update.message.forward_from_chat.id,
                    'type': update.message.forward_from_chat.type,
                    'title': update.message.forward_from_chat.title,
                    'username': update.message.forward_from_chat.username,
                }
                return NF_GETKEYWORDS
            else:
                update.message.reply_text("Follow the instructions and try again!"
                                          '\nTo cancel this process, use /cancel',
                                          parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
                return NF_GETSOURCEID_TYPE

        # ------------ USERS_LEVEL -------------
        # --------- UNAUTHORIZED_LEVEL ---------
        # --------------------------------------
    except Exception as e:
        logger.error(str(e))
        update.message.reply_text("Follow the instructions and try again!\n```{}```".format(str(e)),
                                  parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def newforward_get_source_id(update, context):
    try:
        auth_level = check_auth(update.effective_chat.id)
        # ------------ ADMIN_LEVEL -------------
        # ------------- MOD_LEVEL --------------
        if auth_level.value >= AuthLevel.MOD.value:
            res_msg = context.bot.getChat(chat_id=update.message.text)
            if res_msg:
                # Preparing message
                txt = 'Source:\n' \
                      f' ℹ️ ID: `{res_msg.id}`\n'
                if res_msg.type:
                    txt += f' ℹ️ Type: {res_msg.type}\n'
                if res_msg.title:
                    txt += f' ℹ️ Title: *{res_msg.title}*\n'
                if res_msg.username:
                    txt += f' ℹ️ Username: `@{res_msg.username}`\n'
                logger.info(txt)
                update.message.reply_text(txt, parse_mode=telegram.ParseMode.MARKDOWN,
                                          reply_markup=ReplyKeyboardRemove())
                update.message.reply_text(
                    'Enter keywords, separate them with comma (,). Use \* for forward everything\n'
                    'Example:\n   books,#music'
                    '\nTo cancel this process, use /cancel',
                    parse_mode=telegram.ParseMode.MARKDOWN,
                    reply_markup=ReplyKeyboardRemove())
                settings.new_rule['from'] = {
                    'id': res_msg.id,
                    'type': res_msg.type,
                    'title': res_msg.title,
                    'username': res_msg.username,
                }
                return NF_GETKEYWORDS
            else:
                update.message.reply_text("Follow the instructions and try again!",
                                          parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
                return newforward_start(update, context)

        # ------------ USERS_LEVEL -------------
        # --------- UNAUTHORIZED_LEVEL ---------
        # --------------------------------------
    except Exception as e:
        logger.error(str(e))
        update.message.reply_text("Follow the instructions and try again!\n```{}```".format(str(e)),
                                  parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
        return newforward_start(update, context)
    return ConversationHandler.END


def newforward_get_keywords(update, context):
    try:
        auth_level = check_auth(update.effective_chat.id)
        # ------------ ADMIN_LEVEL -------------
        # ------------- MOD_LEVEL --------------
        if auth_level.value >= AuthLevel.MOD.value:
            keywords_str = update.message.text
            keywords = keywords_str.split(',')
            if len(keywords) > 0:
                # Preparing message
                txt = f'Keywords: {len(keywords)}\n'
                for k in keywords:
                    if k == '*':
                        txt += ' ▪️️ `*` _(Everything)_\n'
                    else:
                        txt += f' ▪️️ `{k}`\n'
                logger.info(txt)
                update.message.reply_text(txt, parse_mode=telegram.ParseMode.MARKDOWN,
                                          reply_markup=ReplyKeyboardRemove())
                settings.new_rule['keywords'] = keywords

                reply_keyboard = [['Forward from Channel'], ['Enter ID/Username']]
                update.message.reply_text('Choose a method to enter your *destination* channel/group',
                                          parse_mode=telegram.ParseMode.MARKDOWN,
                                          reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
                return NF_GETDESTINATION_TYPE
            else:
                update.message.reply_text("Follow the instructions and try again!",
                                          parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
                return newforward_start(update, context)

        # ------------ USERS_LEVEL -------------
        # --------- UNAUTHORIZED_LEVEL ---------
        # --------------------------------------
    except Exception as e:
        logger.error(str(e))
        update.message.reply_text("Follow the instructions and try again!\n```{}```".format(str(e)),
                                  parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
        return newforward_start(update, context)
    return ConversationHandler.END


def newforward_get_destination_type(update, context):
    logger.info("Input type: %s", update.message.text)
    if update.message.text == 'Forward from Channel':
        update.message.reply_text(f'*{update.message.text}*\n'
                                  'Forward message from *destination* channel.\n'
                                  '(this method is not working with groups)\n'
                                  '\nTo cancel this process, use /cancel',
                                  parse_mode=telegram.ParseMode.MARKDOWN,
                                  reply_markup=ReplyKeyboardRemove())
        return NF_GETDESTINATION_FORWARD
    elif update.message.text == 'Enter ID/Username':
        update.message.reply_text(f'*{update.message.text}*\n'
                                  'Enter id/username of  *destination* channel/group:',
                                  parse_mode=telegram.ParseMode.MARKDOWN,
                                  reply_markup=ReplyKeyboardRemove())
        return NF_GETDESTINATION_ID
    else:
        reply_keyboard = [['Forward from Channel'], ['Enter ID/Username']]
        update.message.reply_text('Try again!',
                                  parse_mode=telegram.ParseMode.MARKDOWN,
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return NF_GETDESTINATION_TYPE


def newforward_get_destination_forward(update, context):
    try:
        auth_level = check_auth(update.effective_chat.id)
        # ------------ ADMIN_LEVEL -------------
        # ------------- MOD_LEVEL --------------
        if auth_level.value >= AuthLevel.MOD.value:
            if update.message.forward_from_chat:
                # Preparing message
                txt = 'Destination:\n' \
                      f' ℹ️ ID: `{update.message.forward_from_chat.id}`\n'
                if update.message.forward_from_chat.type:
                    txt += f' ℹ️ Type: {update.message.forward_from_chat.type}\n'
                if update.message.forward_from_chat.title:
                    txt += f' ℹ️ Title: *{update.message.forward_from_chat.title}*\n'
                if update.message.forward_from_chat.username:
                    txt += f' ℹ️ Username: `{update.message.forward_from_chat.username}`\n'
                logger.info(txt)
                update.message.reply_text(txt, parse_mode=telegram.ParseMode.MARKDOWN,
                                          reply_markup=ReplyKeyboardRemove())
                settings.new_rule['to'] = {
                    'id': update.message.forward_from_chat.id,
                    'type': update.message.forward_from_chat.type,
                    'title': update.message.forward_from_chat.title,
                    'username': update.message.forward_from_chat.username,
                }
                reply_keyboard = [['Yes'], ['No']]
                update.message.reply_text(
                    f'*New Forward Rule:\n```{json.dumps(settings.new_rule, indent=2, sort_keys=True)}```\n\nAre you sure you want to add this?',
                    parse_mode=telegram.ParseMode.MARKDOWN,
                    reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
                return NF_VERIFY
            else:
                update.message.reply_text("Follow the instructions and try again!"
                                          '\nTo cancel this process, use /cancel',
                                          parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
                return NF_GETDESTINATION_TYPE

        # ------------ USERS_LEVEL -------------
        # --------- UNAUTHORIZED_LEVEL ---------
        # --------------------------------------
    except Exception as e:
        logger.error(str(e))
        update.message.reply_text("Follow the instructions and try again!\n```{}```".format(str(e)),
                                  parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def newforward_get_destination_id(update, context):
    try:
        auth_level = check_auth(update.effective_chat.id)
        # ------------ ADMIN_LEVEL -------------
        # ------------- MOD_LEVEL --------------
        if auth_level.value >= AuthLevel.MOD.value:
            res_msg = context.bot.getChat(chat_id=update.message.text)
            if res_msg:
                # Preparing message
                txt = 'Destination:\n' \
                      f' ℹ️ ID: `{res_msg.id}`\n'
                if res_msg.type:
                    txt += f' ℹ️ Type: {res_msg.type}\n'
                if res_msg.title:
                    txt += f' ℹ️ Title: *{res_msg.title}*\n'
                if res_msg.username:
                    txt += f' ℹ️ Username: `@{res_msg.username}`\n'
                logger.info(txt)
                update.message.reply_text(txt, parse_mode=telegram.ParseMode.MARKDOWN,
                                          reply_markup=ReplyKeyboardRemove())
                settings.new_rule['to'] = {
                    'id': res_msg.id,
                    'type': res_msg.type,
                    'title': res_msg.title,
                    'username': res_msg.username,
                }
                reply_keyboard = [['Yes'], ['No']]
                update.message.reply_text(
                    f'*New Forward Rule*:\n```{json.dumps(settings.new_rule, indent=2, sort_keys=True)}```\n\nAre you sure you want to add this?',
                    parse_mode=telegram.ParseMode.MARKDOWN,
                    reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
                return NF_VERIFY
            else:
                update.message.reply_text("Follow the instructions and try again!",
                                          parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
                return NF_GETDESTINATION_TYPE

        # ------------ USERS_LEVEL -------------
        # --------- UNAUTHORIZED_LEVEL ---------
        # --------------------------------------
    except Exception as e:
        logger.error(str(e))
        update.message.reply_text("Follow the instructions and try again!\n```{}```".format(str(e)),
                                  parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
        return NF_GETDESTINATION_TYPE
    return ConversationHandler.END


def newforward_verify(update, context):
    try:
        auth_level = check_auth(update.effective_chat.id)
        # ------------ ADMIN_LEVEL -------------
        # ------------- MOD_LEVEL --------------
        if auth_level.value >= AuthLevel.MOD.value:
            if update.message.text == 'Yes':
                settings.new_rule['uuid'] = str(uuid.uuid4())
                settings.forward_rules.append(settings.new_rule)
                settings.save_json_settings(os.path.join(os.path.dirname(sys.argv[0]), 'settings.json'))
                settings.new_rule = {}
                update.message.reply_text("New Forward Rule added and saved to disk.",
                                          parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
            else:
                settings.new_rule = {}
                update.message.reply_text("Canceled.",
                                          parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())

        # ------------ USERS_LEVEL -------------
        # --------- UNAUTHORIZED_LEVEL ---------
        # --------------------------------------
    except Exception as e:
        logger.error(str(e))
        update.message.reply_text("Follow the instructions and try again!\n```{}```".format(str(e)),
                                  parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
        return NF_GETDESTINATION_TYPE
    return ConversationHandler.END


def cancel_conversation(update, context):
    # Reset new rule data
    settings.new_rule = {}
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


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


def cmd_manage_bot(update, context):
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


def cmd_newforward(update, context):
    # reply_keyboard = [['Boy', 'Girl', 'Other']]
    # update.message.reply_text(
    #     'Hi! My name is Professor Bot. I will hold a conversation with you. '
    #     'Send /cancel to stop talking to me.\n\n'
    #     'Are you a boy or a girl?',
    #     reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    auth_level = check_auth(update.effective_chat.id)
    # ------------ ADMIN_LEVEL -------------
    # ------------- MOD_LEVEL --------------
    if auth_level.value >= AuthLevel.MOD.value:
        return newforward_start(update, context)
    # ------------ USERS_LEVEL -------------
    # --------- UNAUTHORIZED_LEVEL ---------
    # --------------------------------------

    return ConversationHandler.END



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
            if fr['from']['id'] == update.effective_chat.id:
                for kw in fr['keywords']:
                    if kw == "*" or kw in update.effective_message.text:
                        context.bot.forward_message(chat_id=fr['to']['id'],
                                                    from_chat_id=update.effective_message.chat_id,
                                                    message_id=update.effective_message.message_id)
                        break
    except Exception as e:
        print("Error: %s" % str(e))


def main():
    # Load settings
    settings.load_json_settings(os.path.join(os.path.dirname(sys.argv[0]), 'settings.json'))

    # Create updater for the bot
    updater = Updater(token=settings.api_token, use_context=True)
    # Dispatcher to registering handlers
    dispatcher = updater.dispatcher

    # Register /start
    cmd_start_handler = CommandHandler('start', cmd_start)
    dispatcher.add_handler(cmd_start_handler)

    # Register /id
    cmd_id_handler = CommandHandler('id', cmd_id)
    dispatcher.add_handler(cmd_id_handler)

    # Register /managebot
    manage_bot_handler = CommandHandler('managebot', cmd_manage_bot)
    dispatcher.add_handler(manage_bot_handler)

    # Register inline buttons
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('newforward', cmd_newforward)],

        states={
            NF_GETSOURCEID_TYPE: [MessageHandler(Filters.regex('^(Forward from Channel|Enter ID/Username)$'),
                                                 newforward_get_source_id_type)],
            NF_GETSOURCEID_FORWARD: [MessageHandler(Filters.forwarded, newforward_get_source_forward)],
            NF_GETSOURCEID_ID: [MessageHandler(Filters.text, newforward_get_source_id)],
            NF_GETKEYWORDS: [MessageHandler(Filters.text, newforward_get_keywords)],
            NF_GETDESTINATION_TYPE: [MessageHandler(Filters.regex('^(Forward from Channel|Enter ID/Username)$'),
                                                    newforward_get_destination_type)],
            NF_GETDESTINATION_FORWARD: [MessageHandler(Filters.forwarded, newforward_get_destination_forward)],
            NF_GETDESTINATION_ID: [MessageHandler(Filters.text, newforward_get_destination_id)],
            NF_VERIFY: [MessageHandler(Filters.regex('^(Yes|No)$'), newforward_verify)],
        },

        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    dispatcher.add_handler(CallbackQueryHandler(buttons))

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    dispatcher.add_handler(conv_handler)

    # Register all messages
    all_msg_handler = MessageHandler(Filters.all, all_msg, message_updates=True, channel_post_updates=True)
    dispatcher.add_handler(all_msg_handler)

    # Parse arguments
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

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    # updater.idle()


if __name__ == '__main__':
    main()
