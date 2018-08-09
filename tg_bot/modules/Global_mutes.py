import html
from io import BytesIO
from typing import Optional, List
 from telegram import Message, Update, Bot, User, Chat
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html
 import tg_bot.modules.sql.global_mutes_sql as sql
from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, STRICT_GMUTE
from tg_bot.modules.helper_funcs.chat_status import user_admin, is_user_admin
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import send_to_list
from tg_bot.modules.sql.users_sql import get_all_chats
 GMUTE_ENFORCE_GROUP = 6
 @run_async
def gmute(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]
     user_id, reason = extract_user_and_text(message, args)
     if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return
     if int(user_id) in SUDO_USERS:
        message.reply_text("I spy, with my little eye... a sudo user war! Why are you guys turning on each other?")
        return
     if int(user_id) in SUPPORT_USERS:
        message.reply_text("OOOH someone's trying to gmute a support user! *grabs popcorn*")
        return
     if user_id == bot.id:
        message.reply_text("-_- So funny, lets gmute myself why don't I? Nice try.")
        return
     try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        message.reply_text(excp.message)
        return
     if user_chat.type != 'private':
        message.reply_text("That's not a user!")
        return
     if sql.is_user_gmuted(user_id):
        if not reason:
            message.reply_text("This user is already gmuted; I'd change the reason, but you haven't given me one...")
            return
         success = sql.update_gmute_reason(user_id, user_chat.username or user_chat.first_name, reason)
        if success:
            message.reply_text("This user is already gmuted; I've gone and updated the gmute reason though!")
        else:
            message.reply_text("Do you mind trying again? I thought this person was gmuted, but then they weren't? "
                               "Am very confused")
         return
     message.reply_text("*Gets duct tape ready* 😉")
     muter = update.effective_user  # type: Optional[User]
    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 "{} is gmuting user {} "
                 "because:\n{}".format(mention_html(muter.id, muter.first_name),
                                       mention_html(user_chat.id, user_chat.first_name), reason or "No reason given"),
                 html=True)
     sql.gmute_user(user_id, user_chat.username or user_chat.first_name, reason)
     chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id
         # Check if this group has disabled gmutes
        if not sql.does_chat_gmute(chat_id):
            continue
         try:
            bot.restrict_chat_member(chat_id, user_id, can_send_messages=False)
        except BadRequest as excp:
            if excp.message == "User is an administrator of the chat":
                pass
            elif excp.message == "Chat not found":
                pass
            elif excp.message == "Not enough rights to restrict/unrestrict chat member":
                pass
            elif excp.message == "User_not_participant":
                pass
            elif excp.message == "Peer_id_invalid":  # Suspect this happens when a group is suspended by telegram.
                pass
            elif excp.message == "Group chat was deactivated":
                pass
            elif excp.message == "Need to be inviter of a user to kick it from a basic group":
                pass
            elif excp.message == "Chat_admin_required":
      
