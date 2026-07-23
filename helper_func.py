#(©)CodeFlix_Bots
#rohit_1888 on Tg #Dont remove this line

import base64
import re
import asyncio
import time
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait
from shortzy import Shortzy
from database.database import *



async def is_subscribed1(filter, client, update):
    if not FORCE_SUB_CHANNEL1:
        return True
    user_id = update.from_user.id
    if user_id in ADMINS:
        return True
    try:
        member = await client.get_chat_member(chat_id = FORCE_SUB_CHANNEL1, user_id = user_id)
    except UserNotParticipant:
        return False

    if not member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
        return False
    else:
        return True

async def is_subscribed2(filter, client, update):
    if not FORCE_SUB_CHANNEL2:
        return True
    user_id = update.from_user.id
    if user_id in ADMINS:
        return True
    try:
        member = await client.get_chat_member(chat_id = FORCE_SUB_CHANNEL2, user_id = user_id)
    except UserNotParticipant:
        return False

    if not member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
        return False
    else:
        return True

async def is_subscribed3(filter, client, update):
    if not FORCE_SUB_CHANNEL3:
        return True
    user_id = update.from_user.id
    if user_id in ADMINS:
        return True
    try:
        member = await client.get_chat_member(chat_id = FORCE_SUB_CHANNEL3, user_id = user_id)
    except UserNotParticipant:
        return False

    if not member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
        return False
    else:
        return True

async def is_subscribed4(filter, client, update):
    if not FORCE_SUB_CHANNEL4:
        return True
    user_id = update.from_user.id
    if user_id in ADMINS:
        return True
    try:
        member = await client.get_chat_member(chat_id = FORCE_SUB_CHANNEL4, user_id = user_id)
    except UserNotParticipant:
        return False

    if not member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
        return False
    else:
        return True


async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string

async def decode(base64_string):
    base64_string = base64_string.strip("=") # links generated before this commit will be having = sign, hence striping them to handle padding errors.
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes) 
    string = string_bytes.decode("ascii")
    return string

async def get_messages(client, message_ids):
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temb_ids = message_ids[total_messages:total_messages+200]
        try:
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except FloodWait as e:
            await asyncio.sleep(e.x)
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except:
            pass
        total_messages += len(temb_ids)
        messages.extend(msgs)
    return messages

async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = "https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern,message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        else:
            if channel_id == client.db_channel.username:
                return msg_id
    else:
        return 0


async def deliver_files(client, messages, user_id, header="", footer="", extra_button=None, concurrency=4):
    """
    Sends a batch of messages to a user concurrently (bounded by `concurrency`),
    transparently retrying once on FloodWait instead of blocking the whole batch
    on a single serial sleep. Preserves per-message ordering in the returned list.

    header/footer: optional strings prepended/appended to each caption.
    extra_button: an InlineKeyboardButton (or None) appended as its own row,
    used for the admin-configured "file button".
    """
    sent = [None] * len(messages)
    semaphore = asyncio.Semaphore(concurrency)

    async def _send(index, msg):
        caption = ""
        if bool(CUSTOM_CAPTION) and bool(msg.document):
            caption = CUSTOM_CAPTION.format(
                previouscaption="" if not msg.caption else msg.caption.html,
                filename=msg.document.file_name
            )
        elif msg.caption:
            caption = msg.caption.html

        if header:
            caption = f"{header}\n{caption}" if caption else header
        if footer:
            caption = f"{caption}\n{footer}" if caption else footer

        reply_markup = msg.reply_markup if DISABLE_CHANNEL_BUTTON else None
        if extra_button is not None:
            rows = list(reply_markup.inline_keyboard) if reply_markup else []
            rows.append([extra_button])
            reply_markup = InlineKeyboardMarkup(rows)

        async with semaphore:
            for attempt in range(2):
                try:
                    sent[index] = await msg.copy(
                        chat_id=user_id,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup,
                        protect_content=PROTECT_CONTENT
                    )
                    break
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    continue
                except Exception as e:
                    print(f"Failed to send message: {e}")
                    break

    await asyncio.gather(*(_send(i, m) for i, m in enumerate(messages)))
    return [m for m in sent if m]


async def broadcast_messages(user_ids, broadcast_msg, delete_after=None, concurrency=15):
    """
    Bounded-concurrency broadcast. Much faster than a serial loop because
    Telegram's per-chat FloodWait only blocks that one send, not the whole
    broadcast, while `concurrency` still keeps us under global rate limits.
    """
    from pyrogram.errors import UserIsBlocked, InputUserDeactivated

    stats = {'total': len(user_ids), 'successful': 0, 'blocked': 0, 'deleted': 0, 'unsuccessful': 0}
    semaphore = asyncio.Semaphore(concurrency)

    async def _send(chat_id):
        async with semaphore:
            for attempt in range(2):
                try:
                    msg = await broadcast_msg.copy(chat_id)
                    if delete_after:
                        await asyncio.sleep(delete_after)
                        try:
                            await msg.delete()
                        except Exception:
                            pass
                    stats['successful'] += 1
                    return
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    continue
                except UserIsBlocked:
                    await del_user(chat_id)
                    stats['blocked'] += 1
                    return
                except InputUserDeactivated:
                    await del_user(chat_id)
                    stats['deleted'] += 1
                    return
                except Exception:
                    stats['unsuccessful'] += 1
                    return
            stats['unsuccessful'] += 1

    await asyncio.gather(*(_send(cid) for cid in user_ids))
    return stats


def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time

async def get_verify_status(user_id):
    verify = await db_verify_status(user_id)
    return verify

async def update_verify_status(user_id, verify_token="", is_verified=False, verified_time=0, link=""):
    current = await db_verify_status(user_id)
    current['verify_token'] = verify_token
    current['is_verified'] = is_verified
    current['verified_time'] = verified_time
    current['link'] = link
    await db_update_verify_status(user_id, current)


async def get_shortlink(url, api, link):
    shortzy = Shortzy(api_key=api, base_site=url)
    link = await shortzy.convert(link)
    return link

def get_exp_time(seconds):
    periods = [('days', 86400), ('hours', 3600), ('mins', 60), ('secs', 1)]
    result = ''
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f'{int(period_value)} {period_name}'
    return result


subscribed1 = filters.create(is_subscribed1)
subscribed2 = filters.create(is_subscribed2)
subscribed3 = filters.create(is_subscribed3)
subscribed4 = filters.create(is_subscribed4)

#rohit_1888 on Tg :
