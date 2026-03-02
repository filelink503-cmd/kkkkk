# plugins/start.py

import random
import humanize
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply, CallbackQuery
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant

# URL encoding ke liye
from urllib.parse import quote_plus

# Apni nayi setting import karein
from info import URL, LOG_CHANNEL, SHORTLINK, FORCE_SUB_CHANNEL, REDIRECT_PAGE_URL 
from TechVJ.util.file_properties import get_name, get_hash, get_media_file_size
from TechVJ.util.human_readable import humanbytes
from database.users_chats_db import db
from utils import temp, get_shortlink

#=====================================================================================
#                        FORCE SUBSCRIBE CHECKER (No changes here)
#=====================================================================================

def get_force_sub_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Update Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")],
    #   [InlineKeyboardButton("📷 Follow on Instagram", url="https://instagram.com/babubhaikundan")],
        [InlineKeyboardButton("✅ I've Joined", callback_data="checksub")]
    ])

async def check_force_sub(client, message):
    try:
        user = await client.get_chat_member(FORCE_SUB_CHANNEL, message.from_user.id)
        if user.status in ("left", "kicked"):
            raise UserNotParticipant
    except UserNotParticipant:
        await message.reply_photo(
            photo=random.choice([
                "https://babubhaikundan.pages.dev/Assets/logo/bbk.png", "https://babubhaikundan.pages.dev/Assets/logo/hacker.png",
                "https://babubhaikundan.pages.dev/Assets/logo/bbk.png", "https://babubhaikundan.pages.dev/Assets/logo/bbk.png",
                "https://babubhaikundan.pages.dev/Assets/logo/hacker.png"
            ]),
            caption=f"<b>Hi {message.from_user.mention},\n\nTo use this bot, you must join our channel first.</b>",
            reply_markup=get_force_sub_buttons()
        )
        return False
    except Exception as e:
        await message.reply(f"🚫 An error occurred: `{e}`", quote=True)
        return False
    return True

#=====================================================================================
#                                CALLBACK HANDLERS (No changes here)
#=====================================================================================

@Client.on_callback_query(filters.regex("^checksub$"))
async def recheck_sub(client, callback_query: CallbackQuery):
    try:
        user = await client.get_chat_member(FORCE_SUB_CHANNEL, callback_query.from_user.id)
        if user.status in ("left", "kicked"):
            await callback_query.answer("💀Abbey yaar channel join kar lo...", show_alert=True)
            return
    except UserNotParticipant:
        await callback_query.answer("💀Abbey yaar channel join kar lo...", show_alert=True)
        return
    except Exception as e:
        await callback_query.answer(f"🚫 Error: {e}", show_alert=True)
        return

    await callback_query.answer("✅ Thank you for joining!", show_alert=False)
    await callback_query.message.delete()
    await client.send_message(callback_query.from_user.id, "Welcome! 🎉\nSend me a file to get started.")

@Client.on_callback_query(filters.regex("^close_data$"))
async def close_handler(client, callback_query: CallbackQuery):
    await callback_query.message.delete()
    await callback_query.answer()

#=====================================================================================
#                                     BOT HANDLERS (No changes here)
#=====================================================================================

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if not await check_force_sub(client, message): return
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention))
    
    images = ["https://babubhaikundan.pages.dev/Assets/logo/bbk.png", "https://babubhaikundan.pages.dev/Assets/logo/hacker.png", "https://babubhaikundan.pages.dev/Assets/logo/bbk.png"]
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 Developer 💀", url="https://t.me/kundan_yadav_bot")],
        [InlineKeyboardButton("📢 Join Update Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]
     #  [InlineKeyboardButton('🆔️ Follow me', url='https://instagram.com/babubhaikundan'), InlineKeyboardButton('▶️ Subscribe', url='https://youtube.com/babubhaikundan')]
    ])
    
    await client.send_photo(
        chat_id=message.chat.id, photo=random.choice(images),
        caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
        reply_markup=buttons, parse_mode=enums.ParseMode.HTML
    )

#=====================================================================================
#               STREAM HANDLER - YAHAN PAR MAIN CHANGES HAIN
#=====================================================================================
@Client.on_message(filters.private & (filters.document | filters.video))
async def stream_start(client, message):
    if not await check_force_sub(client, message): return

    file = getattr(message, message.media.value)
    file_id = file.file_id
    user_id = message.from_user.id
    username = message.from_user.mention 

    log_msg = await client.send_cached_media(chat_id=LOG_CHANNEL, file_id=file_id)
    
    file_name = get_name(log_msg) 
    
    # --- MONETIZATION LOGIC START ---
    # 1. Original video links banayein
    original_stream_url = f"{URL}watch/{str(log_msg.id)}/{quote_plus(file_name)}?hash={get_hash(log_msg)}"
    original_download_url = f"{URL}{str(log_msg.id)}/{quote_plus(file_name)}?hash={get_hash(log_msg)}"

    # 2. Original links ko URL-encode karein taaki wo URL parameter mein sahi se pass ho sakein
    encoded_stream_url = quote_plus(original_stream_url)
    encoded_download_url = quote_plus(original_download_url)
    
    # 3. Monetized redirect link banayein apne `redirect.html` page ka use karke
    monetized_stream_url = f"{REDIRECT_PAGE_URL}?url={encoded_stream_url}"
    monetized_download_url = f"{REDIRECT_PAGE_URL}?url={encoded_download_url}"
    # --- MONETIZATION LOGIC END ---

    # Ab user ko bhejne ke liye final links taiyaar karein
    final_stream_url = monetized_stream_url
    final_download_url = monetized_download_url
    
    # Agar shortlink enabled hai, to upar banaye gaye monetized link ko short karein
    if SHORTLINK:
        final_stream_url = await get_shortlink(monetized_stream_url)
        final_download_url = await get_shortlink(monetized_download_url)
        
    await log_msg.reply_text(
        text=f"•• ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ ꜰᴏʀ ɪᴅ #{user_id} \n•• ᴜꜱᴇʀɴᴀᴍᴇ : {username} \n\n•• ᖴᎥᒪᗴ Nᗩᗰᗴ : {file_name}",
        quote=True, disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Fast Download 🚀", url=final_download_url)],
            [InlineKeyboardButton('🖥️ Watch online 🖥️', url=final_stream_url)]
        ])
    )

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("sᴛʀᴇᴀᴍ 🖥", url=final_stream_url), InlineKeyboardButton("ᴅᴏᴡɴʟᴏᴀᴅ 📥", url=final_download_url)],
        [InlineKeyboardButton("📢 Join", url=f"https://t.me/{FORCE_SUB_CHANNEL}"), InlineKeyboardButton("Close ❌️", callback_data="close_data")],
        [InlineKeyboardButton("📞Contact Developer💀", url="https://t.me/kundan_yadav_bot")]
    ])

    msg_text = """<i><u>𝗬𝗼𝘂𝗿 𝗟𝗶𝗻𝗸 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 !</u></i>\n\n<b>📂 Fɪʟᴇ ɴᴀᴍᴇ :</b> {}\n\n<b>📦 Fɪʟᴇ ꜱɪᴢᴇ :</b> <i>{}</i>\n\n<b>📥 Dᴏᴡɴʟᴏᴀᴅ :</b> <strong>{}</strong>\n\n<b> 🖥ᴡᴀᴛᴄʜ  :</b> <strong>{}</strong>\n\n<b>🚸 Nᴏᴛᴇ : ʟɪɴᴋ ᴡᴏɴ'ᴛ ᴇxᴘɪʀᴇ ᴛɪʟʟ ɪ ᴅᴇʟᴇᴛᴇ</b>"""

    await message.reply_text(
        text=msg_text.format(file_name, humanbytes(get_media_file_size(message)), final_download_url, final_stream_url), 
        quote=True, disable_web_page_preview=True, reply_markup=reply_markup
    )
