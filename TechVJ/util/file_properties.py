# TechVJ/util/file_properties.py - FINAL GUARANTEED FIX
# ✅ get_file_ids ab direct get_name() use karega
# ✅ Naam kabhi bhi None nahi hoga

from pyrogram import Client
from typing import Any, Optional
from pyrogram.types import Message
from pyrogram.file_id import FileId
from pyrogram.raw.types.messages import Messages
from TechVJ.server.exceptions import FIleNotFound

async def parse_file_id(message: "Message") -> Optional[FileId]:
    media = get_media_from_message(message)
    if media:
        return FileId.decode(media.file_id)

async def parse_file_unique_id(message: "Messages") -> Optional[str]:
    media = get_media_from_message(message)
    if media:
        return media.file_unique_id

async def get_file_ids(client: Client, chat_id: int, id: int) -> Optional[FileId]:
    message = await client.get_messages(chat_id, id)
    if message.empty:
        raise FIleNotFound
    media = get_media_from_message(message)
    file_unique_id = await parse_file_unique_id(message)
    file_id = await parse_file_id(message)
    
    # ✅ SABSE BADA CHANGE: Yaha hum direct get_name() call kar rahe hain
    # Isse agar video ka naam nahi bhi hai, to wo 'video.mp4' ban kar hi aayega
    setattr(file_id, "file_size", getattr(media, "file_size", 0))
    setattr(file_id, "mime_type", getattr(media, "mime_type", "") or "")
    setattr(file_id, "file_name", get_name(message))  # 🔥 Fixed Here
    setattr(file_id, "unique_id", file_unique_id)
    return file_id

def get_media_from_message(message: "Message") -> Any:
    media_types = (
        "audio",
        "document",
        "photo",
        "sticker",
        "animation",
        "video",
        "voice",
        "video_note",
    )
    for attr in media_types:
        media = getattr(message, attr, None)
        if media:
            return media

def get_hash(media_msg: Message) -> str:
    media = get_media_from_message(media_msg)
    return getattr(media, "file_unique_id", "")[:6]

def get_name(media_msg: Message) -> str:
    """
    Safely get file name. Handles cases where file_name is None.
    """
    media = get_media_from_message(media_msg)
    
    # Step 1: Get name safely
    name = getattr(media, 'file_name', "") or ""
    
    # Step 2: If name is still empty (common for Telegram Videos), generate one
    if not name:
        mime = getattr(media, "mime_type", "") or ""
        if "video" in mime:
            name = "video.mp4"
        elif "audio" in mime:
            name = "audio.mp3"
        elif "image" in mime:
            name = "image.jpg"
        else:
            name = "file"
            
    # Step 3: Force String (Quote_plus error killer)
    return str(name)

def get_media_file_size(m):
    media = get_media_from_message(m)
    return getattr(media, "file_size", 0)
