# BabuBhaiKundan/util/render_template.py

import jinja2
from info import *
from BabuBhaiKundan.bot import BabuBhaiKundanBot
from BabuBhaiKundan.util.human_readable import humanbytes
from BabuBhaiKundan.util.file_properties import get_file_ids
import urllib.parse
import logging
import aiohttp


async def render_page(id, secure_hash, src=None, chat_id=None):

    if chat_id is None:
        chat_id = int(LOG_CHANNEL)
    else:
        chat_id = int(chat_id)

    file = await BabuBhaiKundanBot.get_messages(chat_id, int(id))
    file_data = await get_file_ids(BabuBhaiKundanBot, chat_id, int(id))

    # ---------------------------------------------------------------
    # 🔥 HASH CHECK
    # ---------------------------------------------------------------
    if file_data.unique_id[:6] != secure_hash:
        logging.debug(f"link hash: {secure_hash} - {file_data.unique_id[:6]}")
        logging.debug(f"Invalid hash for message with - ID {id}")
        raise InvalidHash   # add hash for direct download file fail
    # ---------------------------------------------------------------

    # ==========================================
    # 🔥 SAFE FILE NAME FIX
    # ==========================================
    try:
        file_name = getattr(file_data, "file_name", "video.mp4")

        if not file_name:
            file_name = "video.mp4"

        if not isinstance(file_name, str):
            file_name = str(file_name)

        encoded_name = urllib.parse.quote_plus(file_name)

    except Exception:
        file_name = "video.mp4"
        encoded_name = "video.mp4"
    # ==========================================

    src = urllib.parse.urljoin(
        URL,
        f"{chat_id}/{id}/{encoded_name}?hash={secure_hash}",
    )

    # ==========================================
    # FILE TYPE DETECTION
    # ==========================================
    tag = file_data.mime_type.split("/")[0].strip()
    file_size = humanbytes(file_data.file_size)

    # 🔥 Player URL variable
    file_url_for_player = src

    if tag in ["video", "audio"]:
        template_file = "BabuBhaiKundan/template/req.html"

        # 🔥 Add play mode for streaming optimization
        file_url_for_player = f"{src}&mode=play"

    else:
        template_file = "BabuBhaiKundan/template/dl.html"

        async with aiohttp.ClientSession() as s:
            async with s.get(src) as u:
                size = u.headers.get("Content-Length")

                if size:
                    file_size = humanbytes(int(size))
                else:
                    file_size = "Unknown"

    # ==========================================
    # LOAD TEMPLATE
    # ==========================================
    with open(template_file) as f:
        template = jinja2.Template(f.read())

    file_name = (file_data.file_name or "video.mp4").replace("_", " ")

    return template.render(
        file_name=file_name,
        file_url=file_url_for_player,
        file_size=file_size,
        file_unique_id=file_data.unique_id,
    )