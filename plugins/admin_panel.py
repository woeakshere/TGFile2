#(©)CodeFlix_Bots - Admin Panel
# Single /admin command with an inline-button menu.

import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from bot import Bot
from config import ADMINS
from database.database import (
    get_settings, update_settings,
    ban_user, unban_user,
    get_link, set_link_disabled, delete_link,
)


def admin_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚫 Ban User", callback_data="adm_ban"),
         InlineKeyboardButton("✅ Unban User", callback_data="adm_unban")],
        [InlineKeyboardButton("📝 Header / Footer", callback_data="adm_hf"),
         InlineKeyboardButton("🖼 Banner", callback_data="adm_banner")],
        [InlineKeyboardButton("🗂 Manage Files", callback_data="adm_files")],
        [InlineKeyboardButton("🎟 Credits & Token", callback_data="adm_credits")],
        [InlineKeyboardButton("🔘 File Button", callback_data="adm_button")],
        [InlineKeyboardButton("ᴄʟᴏꜱᴇ", callback_data="adm_close")],
    ])


BACK_BTN = InlineKeyboardMarkup([[InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="adm_back")]])


@Bot.on_message(filters.command('admin') & filters.private & filters.user(ADMINS))
async def admin_panel(client: Bot, message: Message):
    await message.reply_text(
        "<b>⚙️ Admin Panel</b>\n\nChoose what you'd like to manage.",
        reply_markup=admin_main_menu()
    )


async def _ask(client, chat_id, prompt, timeout=90):
    """Wrapper around pyromod's client.ask that swallows timeouts cleanly."""
    try:
        return await client.ask(text=prompt, chat_id=chat_id, filters=filters.text, timeout=timeout)
    except asyncio.TimeoutError:
        return None
    except Exception:
        return None


@Bot.on_callback_query(filters.regex(r"^adm_") & filters.user(ADMINS))
async def admin_callbacks(client: Bot, query: CallbackQuery):
    data = query.data
    chat_id = query.from_user.id
    await query.answer()

    if data == "adm_close":
        return await query.message.delete()

    if data == "adm_back":
        return await query.message.edit_text(
            "<b>⚙️ Admin Panel</b>\n\nChoose what you'd like to manage.",
            reply_markup=admin_main_menu()
        )

    # ---------------- BAN / UNBAN ----------------
    if data == "adm_ban":
        resp = await _ask(client, chat_id, "Send the user ID to <b>ban</b> (or /cancel):")
        if not resp or resp.text.strip() == "/cancel":
            return
        try:
            uid = int(resp.text.strip())
        except ValueError:
            return await resp.reply("That's not a valid user ID.")
        await ban_user(uid)
        return await resp.reply(f"<b>{uid}</b> has been banned.", reply_markup=admin_main_menu())

    if data == "adm_unban":
        resp = await _ask(client, chat_id, "Send the user ID to <b>unban</b> (or /cancel):")
        if not resp or resp.text.strip() == "/cancel":
            return
        try:
            uid = int(resp.text.strip())
        except ValueError:
            return await resp.reply("That's not a valid user ID.")
        await unban_user(uid)
        return await resp.reply(f"<b>{uid}</b> has been unbanned.", reply_markup=admin_main_menu())

    # ---------------- HEADER / FOOTER ----------------
    if data == "adm_hf":
        settings = await get_settings()
        text = (
            f"<b>Current Header:</b>\n<code>{settings['header'] or 'None'}</code>\n\n"
            f"<b>Current Footer:</b>\n<code>{settings['footer'] or 'None'}</code>"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Set Header", callback_data="adm_sethdr"),
             InlineKeyboardButton("Set Footer", callback_data="adm_setftr")],
            [InlineKeyboardButton("Clear Header", callback_data="adm_clrhdr"),
             InlineKeyboardButton("Clear Footer", callback_data="adm_clrftr")],
            [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="adm_back")]
        ])
        return await query.message.edit_text(text, reply_markup=kb)

    if data in ("adm_sethdr", "adm_setftr"):
        which = "header" if data == "adm_sethdr" else "footer"
        resp = await _ask(client, chat_id, f"Send the new {which} text (HTML allowed), or /cancel:", timeout=180)
        if not resp or resp.text.strip() == "/cancel":
            return
        await update_settings(**{which: resp.text})
        return await resp.reply(f"{which.capitalize()} updated.", reply_markup=admin_main_menu())

    if data in ("adm_clrhdr", "adm_clrftr"):
        which = "header" if data == "adm_clrhdr" else "footer"
        await update_settings(**{which: ""})
        return await query.answer(f"{which.capitalize()} cleared.", show_alert=True)

    # ---------------- BANNER ----------------
    if data == "adm_banner":
        settings = await get_settings()
        text = f"<b>Current banner:</b> {'Custom banner set' if settings['banner'] else 'None (using START_PIC)'}"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Set Banner", callback_data="adm_setbanner"),
             InlineKeyboardButton("Clear Banner", callback_data="adm_clrbanner")],
            [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="adm_back")]
        ])
        return await query.message.edit_text(text, reply_markup=kb)

    if data == "adm_setbanner":
        try:
            resp = await client.ask(text="Send the new banner as a photo, or send an image URL (or /cancel):",
                                     chat_id=chat_id, timeout=180)
        except asyncio.TimeoutError:
            return
        if resp.text and resp.text.strip() == "/cancel":
            return
        if resp.photo:
            await update_settings(banner=resp.photo.file_id)
        elif resp.text:
            await update_settings(banner=resp.text.strip())
        else:
            return await resp.reply("Send a photo or a URL.")
        return await resp.reply("Banner updated.", reply_markup=admin_main_menu())

    if data == "adm_clrbanner":
        await update_settings(banner="")
        return await query.answer("Banner cleared.", show_alert=True)

    # ---------------- CREDITS & TOKEN ----------------
    if data == "adm_credits":
        settings = await get_settings()
        text = (
            f"<b>Free credits (no-token file pulls):</b> {settings['free_credits']}\n"
            f"<b>Token validity:</b> ~{round(settings['token_duration'] / 3600, 1)}h "
            f"({settings['token_duration']}s)"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Set Free Credits", callback_data="adm_setcredits")],
            [InlineKeyboardButton("Set Token Duration", callback_data="adm_settoken")],
            [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="adm_back")]
        ])
        return await query.message.edit_text(text, reply_markup=kb)

    if data == "adm_setcredits":
        resp = await _ask(client, chat_id, "Send number of free credits per verification cycle (e.g. 1), or /cancel:")
        if not resp or resp.text.strip() == "/cancel":
            return
        try:
            val = int(resp.text.strip())
        except ValueError:
            return await resp.reply("Send a whole number.")
        await update_settings(free_credits=val)
        return await resp.reply(f"Free credits set to {val}.", reply_markup=admin_main_menu())

    if data == "adm_settoken":
        resp = await _ask(client, chat_id, "Send token validity in <b>hours</b> (e.g. 24), or /cancel:")
        if not resp or resp.text.strip() == "/cancel":
            return
        try:
            hours = float(resp.text.strip())
        except ValueError:
            return await resp.reply("Send a number.")
        await update_settings(token_duration=int(hours * 3600))
        return await resp.reply(f"Token validity set to {hours}h.", reply_markup=admin_main_menu())

    # ---------------- FILE BUTTON ----------------
    if data == "adm_button":
        settings = await get_settings()
        status = "ON ✅" if settings['button_enabled'] else "OFF ❌"
        text = (
            f"<b>File button:</b> {status}\n"
            f"<b>Text:</b> {settings['button_text'] or 'None'}\n"
            f"<b>URL:</b> {settings['button_url'] or 'None'}"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Toggle On/Off", callback_data="adm_togglebtn")],
            [InlineKeyboardButton("Set Button", callback_data="adm_setbtn")],
            [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="adm_back")]
        ])
        return await query.message.edit_text(text, reply_markup=kb)

    if data == "adm_togglebtn":
        settings = await get_settings()
        await update_settings(button_enabled=not settings['button_enabled'])
        return await query.answer("Toggled.", show_alert=True)

    if data == "adm_setbtn":
        resp = await _ask(
            client, chat_id,
            "Send button text and URL separated by | \nExample: <code>Join Channel|https://t.me/yourchannel</code>\n(or /cancel)",
            timeout=180
        )
        if not resp or resp.text.strip() == "/cancel":
            return
        if "|" not in resp.text:
            return await resp.reply("Format must be: text|url")
        text, url = resp.text.split("|", 1)
        await update_settings(button_text=text.strip(), button_url=url.strip(), button_enabled=True)
        return await resp.reply("Button saved and enabled.", reply_markup=admin_main_menu())

    # ---------------- MANAGE FILES ----------------
    if data == "adm_files":
        resp = await _ask(client, chat_id, "Send the file link (or just the code after ?start=) to manage, or /cancel:", timeout=180)
        if not resp or resp.text.strip() == "/cancel":
            return
        code = resp.text.strip().split("start=")[-1].strip()
        link_doc = await get_link(code)
        if not link_doc:
            return await resp.reply(
                "No record found for that link.\n(Links generated before this update aren't tracked.)",
                reply_markup=admin_main_menu()
            )
        status = "Disabled 🚫" if link_doc.get('disabled') else "Active ✅"
        info = (
            f"<b>Link code:</b> <code>{code}</code>\n"
            f"<b>Status:</b> {status}\n"
            f"<b>Files:</b> {len(link_doc['ids'])}\n"
            f"<b>Hits:</b> {link_doc.get('hits', 0)}"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "Disable" if not link_doc.get('disabled') else "Enable",
                callback_data=f"adf_t_{code}"
            )],
            [InlineKeyboardButton("🗑 Delete", callback_data=f"adf_d_{code}")],
            [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="adm_back")]
        ])
        return await resp.reply(info, reply_markup=kb)


@Bot.on_callback_query(filters.regex(r"^adf_") & filters.user(ADMINS))
async def admin_file_callbacks(client: Bot, query: CallbackQuery):
    data = query.data
    action, code = data.split("_", 2)[1], data.split("_", 2)[2]

    if action == "t":
        link_doc = await get_link(code)
        if not link_doc:
            return await query.answer("Not found.", show_alert=True)
        await set_link_disabled(code, not link_doc.get('disabled'))
        return await query.answer("Updated.", show_alert=True)

    if action == "d":
        await delete_link(code)
        await query.answer("Deleted.", show_alert=True)
        return await query.message.edit_text("Link record deleted.", reply_markup=admin_main_menu())
