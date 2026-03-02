# plugins/start.py - FIXED VERSION
# ✅ URL generation now includes LOG_CHANNEL
# ✅ Removed duplicate stats handler

import random
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from urllib.parse import quote_plus

from info import (
    LOG_CHANNEL, FORCE_SUB_CHANNEL, REDIRECT_PAGE_URL,
    PREMIUM_PRICE, FREE_USER_DAILY_LIMIT, URL,
    DEPLOYMENT_MODE, WORKER_URLS, ENABLE_USER_COMMANDS,
    ENABLE_LOAD_BALANCING
)
from TechVJ.util.file_properties import get_name, get_hash, get_media_file_size
from TechVJ.util.human_readable import humanbytes
from database.users_chats_db import db
from utils import temp, get_shortlink

# Load balancer (only used in master mode)
if ENABLE_LOAD_BALANCING:
    from TechVJ.util.load_balancer import load_balancer


def get_force_sub_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Update Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")],
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
                "https://babubhaikundan.pages.dev/Assets/logo/bbk.png",
                "https://babubhaikundan.pages.dev/Assets/logo/hacker.png",
            ]),
            caption=f"<b>Hi {message.from_user.mention},\n\nTo use this bot, you must join our channel first.</b>",
            reply_markup=get_force_sub_buttons()
        )
        return False
    except Exception as e:
        await message.reply(f"🚫 An error occurred: `{e}`", quote=True)
        return False
    return True


@Client.on_callback_query(filters.regex("^checksub$"))
async def recheck_sub(client, callback_query: CallbackQuery):
    try:
        user = await client.get_chat_member(FORCE_SUB_CHANNEL, callback_query.from_user.id)
        if user.status in ("left", "kicked"):
            await callback_query.answer("💀Abbey yaar Join Channel then use my Bot...", show_alert=True)
            return
    except UserNotParticipant:
        await callback_query.answer("💀Abbey yaar Join my Channel...", show_alert=True)
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


# ═══════════════════════════════════════════════════════════════
# START COMMAND (Only enabled if ENABLE_USER_COMMANDS is True)
# ═══════════════════════════════════════════════════════════════

if ENABLE_USER_COMMANDS:
    
    @Client.on_message(filters.command("start") & filters.incoming)
    async def start(client, message):
        if not await check_force_sub(client, message):
            return
        if not await db.is_user_exist(message.from_user.id):
            await db.add_user(message.from_user.id, message.from_user.first_name)
            await client.send_message(
                LOG_CHANNEL, 
                script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention)
            )

        images = [
            "https://babubhaikundan.pages.dev/Assets/logo/bbk.png",
            "https://babubhaikundan.pages.dev/Assets/logo/hacker.png"
        ]
        
        # Show deployment mode in start message (optional)
        mode_badge = ""
        if DEPLOYMENT_MODE == 'master':
            mode_badge = f"\n\n🌐 Multi-Server Mode ({len(WORKER_URLS)} servers)"
        elif DEPLOYMENT_MODE == 'single':
            mode_badge = "\n\n🖥️ Single Server Mode"
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 Premium Plans", callback_data="buy_premium")],
            [InlineKeyboardButton("📞 Developer 💀", url="https://t.me/kundan_yadav_bot")],
            [InlineKeyboardButton("📢 Join Update Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]
        ])

        await client.send_photo(
            chat_id=message.chat.id,
            photo=random.choice(images),
            caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME) + mode_badge,
            reply_markup=buttons,
            parse_mode=enums.ParseMode.HTML
        )



# ✅ YAHAN ADD KARO - BILKUL USKE UPAR, Direct link ko player se stream karne ka /stream command 

@Client.on_message(filters.command("stream") & filters.private)
async def external_stream_cmd(client, message):
    try:
        full_text = message.text.split(None, 1)[1].strip()
    except:
        await message.reply(
            "❌ Usage:\n"
            "`/stream <url>` — naam URL se auto detect\n"
            "`/stream <url> | <custom name>` — khud naam do\n\n"
            "Examples:\n"
            "`/stream https://example.com/video.mp4`\n"
            "`/stream https://example.com/v?id=123 | Avengers Endgame`"
        )
        return
    
    import urllib.parse
    
    # ✅ Check karo | hai ya nahi
    if "|" in full_text:
        parts = full_text.split("|", 1)
        url = parts[0].strip()
        file_name = parts[1].strip()
    else:
        url = full_text.strip()
        # URL se auto detect karo
        raw_name = url.split("/")[-1].split("?")[0]
        file_name = raw_name if raw_name and "." in raw_name else "video.mp4"
    
    # Safety check
    if not file_name:
        file_name = "video.mp4"
    
    encoded_name = urllib.parse.quote(file_name, safe='')
    player_url = f"{URL}stream?url={urllib.parse.quote(url, safe='')}&name={encoded_name}"
    final_url = f"{REDIRECT_PAGE_URL}?url={urllib.parse.quote(player_url, safe='')}"
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🖥️ Open in BBK Player", url=final_url)]
    ])
    
    await message.reply(
        f"✅ **Stream Link Ready!**\n\n"
        f"📂 File: `{file_name}`\n\n"
        f"👇 Click to play:",
        reply_markup=buttons,
        disable_web_page_preview=True
    )





@Client.on_message(filters.command("iframe") & filters.private)
async def iframe_cmd(client, message):
    try:
        full_text = message.text.split(None, 1)[1].strip()
    except:
        await message.reply(
            "❌ Usage:\n"
            "`/iframe <url>` — site iframe mein khulegi\n"
            "`/iframe <url> | <title>` — custom title do\n\n"
            "Example:\n"
            "`/iframe https://babubhaikundan.pages.dev/ | India vs WI Live`"
        )
        return

    import urllib.parse

    if "|" in full_text:
        parts = full_text.split("|", 1)
        url   = parts[0].strip()
        title = parts[1].strip()
    else:
        url   = full_text.strip()
        title = "Live Stream"

    encoded_title = urllib.parse.quote(title, safe='')
    iframe_url = f"{URL}iframe?url={urllib.parse.quote(url, safe='')}&name={encoded_title}"
    final_url  = f"{REDIRECT_PAGE_URL}?url={urllib.parse.quote(iframe_url, safe='')}"

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 Watch Live", url=final_url)]
    ])

    await message.reply(
        f"✅ **Iframe Link Ready!**\n\n"
        f"📺 Title: `{title}`\n"
        f"🌐 Site: `{url[:50]}...`\n\n"
        f"👇 Click to open:",
        reply_markup=buttons,
        disable_web_page_preview=True
    )
    
    


# ═══════════════════════════════════════════════════════════════
# FILE HANDLER (Works in all modes)
# ═══════════════════════════════════════════════════════════════

@Client.on_message(filters.private & (filters.document | filters.video))
async def stream_start(client, message):
    """
    ✅ FIXED: URLs now properly include LOG_CHANNEL to avoid PEER_ID_INVALID
    """
    
    # Worker bots don't accept files
    if DEPLOYMENT_MODE == 'worker':
        return
    
    if not await check_force_sub(client, message):
        return

    user_id = message.from_user.id

    try:
        await db._ensure_user_doc(user_id)
        if not await db.is_user_exist(user_id):
            await db.add_user(user_id, message.from_user.first_name)

        is_premium = await db.check_premium(user_id)

        # Daily limit check (atomic)
        if not is_premium:
            allowed = await db.check_and_increment_daily_limit(user_id)

            if not allowed:
                limit_text = f"""
⚠️ **Daily Limit Exceeded!** ⚠️

📊 You've used all {FREE_USER_DAILY_LIMIT} free links today.
⏰ Limit resets at 12:00 AM IST

💎 **Want Unlimited Access?**
Upgrade to Premium for just ₹{PREMIUM_PRICE}/month!

✨ **Premium Benefits:**
✅ Unlimited file streaming
✅ No daily limits
✅ Priority support
✅ High-speed downloads

Click below to upgrade now! 👇
"""
                buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"💎 Buy Premium - ₹{PREMIUM_PRICE}/month", callback_data="buy_premium")],
                    [InlineKeyboardButton("📊 Check Usage", callback_data="free_limits")]
                ])

                await message.reply_photo(
                    photo="https://babubhaikundan.pages.dev/Assets/logo/bbk.png",
                    caption=limit_text,
                    reply_markup=buttons
                )
                return

        # File processing
        file = getattr(message, message.media.value)
        file_id = file.file_id
        username = message.from_user.mention

        try:
            log_msg = await client.send_cached_media(chat_id=LOG_CHANNEL, file_id=file_id)
        except Exception as e:
            await message.reply(f"❌ Error uploading file. Contact admin.\nError: {e}")
            return

        file_name = get_name(log_msg)
        file_hash = get_hash(log_msg)
        
        if not file_name:
            file_name = "file"  # Default name if None
        elif isinstance(file_name, bytes):
            file_name = file_name.decode('utf-8', errors='ignore')  # Bytes to string
            file_name = str(file_name)  # Ensure it's string

        # ═══════════════════════════════════════════════════════════
        # ✅ FIXED: URL GENERATION NOW INCLUDES LOG_CHANNEL
        # ═══════════════════════════════════════════════════════════

        if ENABLE_LOAD_BALANCING:
            # MULTI-INSTANCE MODE: Use load balancer
            worker_url = load_balancer.get_worker_url(user_id=user_id)
            
            # ✅ FIX: Include LOG_CHANNEL in URL
            original_stream_url = f"{worker_url}watch/{LOG_CHANNEL}/{log_msg.id}/{quote_plus(file_name)}?hash={file_hash}"
            original_download_url = f"{worker_url}{LOG_CHANNEL}/{log_msg.id}/{quote_plus(file_name)}?hash={file_hash}"
            
            # Get worker info for display
            worker_info = load_balancer.get_worker_info(worker_url)
            server_name = worker_info['name']
            
        else:
            # SINGLE-INSTANCE MODE: Use own URL
            # ✅ FIX: Include LOG_CHANNEL in URL
            original_stream_url = f"{URL}watch/{LOG_CHANNEL}/{log_msg.id}/{quote_plus(file_name)}?hash={file_hash}"
            original_download_url = f"{URL}{LOG_CHANNEL}/{log_msg.id}/{quote_plus(file_name)}?hash={file_hash}"
            server_name = "Main Server"


        # Monetization redirect
        monetized_stream_url = f"{REDIRECT_PAGE_URL}?url={quote_plus(original_stream_url)}"
        monetized_download_url = f"{REDIRECT_PAGE_URL}?url={quote_plus(original_download_url)}"

        final_stream_url = monetized_stream_url
        final_download_url = monetized_download_url

        # Shortlink (optional)
        from info import SHORTLINK
        if SHORTLINK:
            try:
                final_stream_url = await get_shortlink(monetized_stream_url)
                final_download_url = await get_shortlink(monetized_download_url)
            except Exception as e:
                print(f"Shortlink error: {e}")

        # Badge and usage
        user_badge = "👑 Premium User" if is_premium else "🆓 Free User"

        if not is_premium:
            daily_used = await db.get_daily_usage(user_id)
            remaining = FREE_USER_DAILY_LIMIT - daily_used
            usage_text = f"\n📊 Today: {daily_used}/{FREE_USER_DAILY_LIMIT} | Left: {remaining}\n"
        else:
            usage_text = "\n♾️ Unlimited Access"

        # Mode indicator
        if DEPLOYMENT_MODE == 'master':
            mode_text = f"🌐 Server: {server_name}"
        else:
            mode_text = f"🌐 Server: {server_name} (100GB)"

        # Log channel message (SINGLE MESSAGE COUNT ✅)
        await log_msg.edit_caption(
    caption=(
        f"•• <b>ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ</b> for <code>#{user_id}</code>\n"
        f"•• <b>ᴜꜱᴇʀ :</b> {username} {user_badge}\n"
        f"•• <b>ꜰɪʟᴇ :</b> <code>{file_name}</code>\n"
        f"••{mode_text}"
    ),
    reply_markup=InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📥 Download", url=final_download_url)],
            [InlineKeyboardButton("🖥️ Stream", url=final_stream_url)]
        ]
    )
)

        # User message
        reply_markup = InlineKeyboardMarkup([
            
            [
                InlineKeyboardButton("📢 Join", url=f"https://t.me/{FORCE_SUB_CHANNEL}"),
                InlineKeyboardButton("💬 𝘋𝘦𝘷𝘦𝘭𝘰𝘱𝘦𝘳", url="https://t.me/kundan_yadav_bot")
            ],
            [InlineKeyboardButton("💎 Buy  Premium", callback_data="buy_premium"),
             InlineKeyboardButton("Close ❌", callback_data="close_data")
            ]
        ])

        msg_text = f"""
<i><u>𝗬𝗼𝘂𝗿 𝗟𝗶𝗻𝗸 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱!</u></i> {user_badge}

<b>📂 Fɪʟᴇ :</b> <code>{file_name}</code>

<b>📦 Sɪᴢᴇ :</b> <code>{humanbytes(get_media_file_size(message))}</code>

<b>📥 Dᴏᴡɴʟᴏᴀᴅ :</b>
{final_download_url}

<b>🖥 Sᴛʀᴇᴀᴍ :</b>
{final_stream_url}

<b>🚸 Nᴏᴛᴇ :</b> <i>Link will not expire until I delete it.</i>
{mode_text}
{usage_text}
"""

        await message.reply_text(
            text=msg_text,
            quote=True,
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )

    except Exception as e:
        print(f"Stream handler error: {e}")
        import traceback
        traceback.print_exc()
        await message.reply(f"❌ Error occurred. Contact admin.\n\nError: {e}")
