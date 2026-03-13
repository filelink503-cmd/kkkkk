import re, math, logging, secrets, mimetypes, time
from info import *
from aiohttp import web
from aiohttp.http_exceptions import BadStatusLine
from BabuBhaiKundan.bot import multi_clients, work_loads, BabuBhaiKundanBot
from BabuBhaiKundan.server.exceptions import FIleNotFound, InvalidHash
from BabuBhaiKundan import StartTime, __version__
from BabuBhaiKundan.util.custom_dl import ByteStreamer
from BabuBhaiKundan.util.time_format import get_readable_time
from BabuBhaiKundan.util.render_template import render_page

routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    """Render welcome page on root URL"""
    try:
        with open("BabuBhaiKundan/template/welcome.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return web.Response(text=html_content, content_type='text/html')
    except FileNotFoundError:
        return web.json_response({
            "bot": "Kundan File Stream Bot",
            "status": "running",
            "message": "Bot is active! Use /start in Telegram"
        })

@routes.get(r"/watch/{path:\S+}", allow_head=True)
async def watch_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        secure_hash = request.rel_url.query.get("hash")
        
        # ----------------------------------------------------------------------
        # 🔥 MULTI-CHANNEL INTEGRATION START
        # ----------------------------------------------------------------------
        
        # Case 1: Multi-Channel Link (/watch/-100xxxx/1234)
        match_multi = re.search(r"^(-?\d+)[/](\d+)", path)
        
        # Case 2: Old Hash Link (/watch/abcdef123)
        match_hash = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        
        # Case 3: Old ID Link (/watch/1234)
        match_id = re.search(r"^(\d+)(?:\/\S+)?", path)

        if match_multi:
            chat_id = int(match_multi.group(1))
            id = int(match_multi.group(2))
        elif match_hash:
            secure_hash = match_hash.group(1)
            id = int(match_hash.group(2))
            chat_id = int(LOG_CHANNEL) # Default to LOG_CHANNEL
        elif match_id:
            id = int(match_id.group(1))
            chat_id = int(LOG_CHANNEL) # Default to LOG_CHANNEL
        else:
            raise FIleNotFound # Invalid Format
            
        # ----------------------------------------------------------------------
        # 🔥 MULTI-CHANNEL INTEGRATION END
        # ----------------------------------------------------------------------

        return web.Response(text=await render_page(id, secure_hash, src=None, chat_id=chat_id), content_type='text/html')
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        pass
    except Exception as e:
        logging.critical(e.with_traceback(None))
        raise web.HTTPInternalServerError(text=str(e))
        


# ✅ YAHAN ADD KARO - BILKUL END MEIN, Ye direct stream ka kaam karta hai

@routes.get("/stream", allow_head=True)
async def external_stream_handler(request: web.Request):
    try:
        file_url = request.rel_url.query.get("url")
        file_name = request.rel_url.query.get("name", "video.mp4")
        
        if not file_url:
            raise web.HTTPBadRequest(text="URL parameter missing")
        
        import jinja2, urllib.parse
        file_url = urllib.parse.unquote(file_url)
        
        with open("BabuBhaiKundan/template/req.html") as f:
            template = jinja2.Template(f.read())
        
        return web.Response(
            text=template.render(
                file_name=file_name,
                file_url=file_url,
                file_size="",
                file_unique_id=""
            ),
            content_type='text/html'
        )
    except Exception as e:
        raise web.HTTPInternalServerError(text=str(e))        
        

@routes.get("/iframe", allow_head=True)
async def iframe_handler(request: web.Request):
    try:
        url = request.rel_url.query.get("url")
        title = request.rel_url.query.get("name", "Live Stream")
        
        if not url:
            raise web.HTTPBadRequest(text="URL parameter missing")
        
        import jinja2, urllib.parse
        url = urllib.parse.unquote(url)
        
        with open("BabuBhaiKundan/template/iframe.html") as f:
            template = jinja2.Template(f.read())
        
        return web.Response(
            text=template.render(
                title=title,
                url=url
            ),
            content_type='text/html'
        )
    except Exception as e:
        raise web.HTTPInternalServerError(text=str(e))       
        
        

@routes.get(r"/{path:\S+}", allow_head=True)
async def stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        secure_hash = request.rel_url.query.get("hash")
        
        # ----------------------------------------------------------------------
        # 🔥 MULTI-CHANNEL INTEGRATION START
        # ----------------------------------------------------------------------

        # Case 1: Multi-Channel Link (/-100xxxx/1234)
        match_multi = re.search(r"^(-?\d+)[/](\d+)", path)
        
        # Case 2: Old Hash Link (/abcdef123)
        match_hash = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        
        # Case 3: Old ID Link (/1234)
        match_id = re.search(r"^(\d+)(?:\/\S+)?", path)

        if match_multi:
            chat_id = int(match_multi.group(1))
            id = int(match_multi.group(2))
        elif match_hash:
            secure_hash = match_hash.group(1)
            id = int(match_hash.group(2))
            chat_id = int(LOG_CHANNEL)
        elif match_id:
            id = int(match_id.group(1))
            chat_id = int(LOG_CHANNEL)
        else:
            raise FIleNotFound

        # ----------------------------------------------------------------------
        # 🔥 MULTI-CHANNEL INTEGRATION END
        # ----------------------------------------------------------------------
        
        return await media_streamer(request, id, secure_hash, chat_id)
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        pass
    except Exception as e:
        logging.critical(e.with_traceback(None))
        raise web.HTTPInternalServerError(text=str(e))

class_cache = {}

# 🔥 Updated: Added chat_id parameter
async def media_streamer(request: web.Request, id: int, secure_hash: str, chat_id: int):
    range_header = request.headers.get("Range", 0)
    
    index = min(work_loads, key=work_loads.get)
    faster_client = multi_clients[index]
    
    if MULTI_CLIENT:
        logging.info(f"Client {index} is now serving {request.remote}")

    if faster_client in class_cache:
        tg_connect = class_cache[faster_client]
        logging.debug(f"Using cached ByteStreamer object for client {index}")
    else:
        logging.debug(f"Creating new ByteStreamer object for client {index}")
        tg_connect = ByteStreamer(faster_client)
        class_cache[faster_client] = tg_connect
        
    logging.debug("before calling get_file_properties")
    
    file_id = await tg_connect.get_file_properties(id, chat_id)
    
 logging.debug("after calling get_file_properties")
    
    # ---------------------------------------------------------------
    # 🔥 ROUTE.PY ME BHI HASH CHECK WAPAS CHALU KARO
    # ---------------------------------------------------------------
    if file_id.unique_id[:6] != secure_hash:
        logging.debug(f"Invalid hash for message with ID {id}")
        raise InvalidHash  # <-- 😡 YAHAN SE BHI '#' HATA DO! 
    # ---------------------------------------------------------------

    
    file_size = file_id.file_size

    # -------------------------------------------------------
    # RANGE HEADER PARSING (SAFE)
    # -------------------------------------------------------
    if range_header:
        try:
            from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
            from_bytes = int(from_bytes)
            until_bytes = int(until_bytes) if until_bytes else file_size - 1
        except Exception:
            from_bytes = 0
            until_bytes = file_size - 1
    else:
        from_bytes = request.http_range.start or 0
        until_bytes = (request.http_range.stop or file_size) - 1


    # -----------------------------------------------------------------
    # 🔥 BABU BHAI SMART CHUNKING SYSTEM (NINJA TECHNIQUE)
    # -----------------------------------------------------------------
    is_playing_online = request.rel_url.query.get("mode") == "play"

    if is_playing_online:
        MAX_CHUNK_LIMIT = 5 * 1024 * 1024
        if (until_bytes - from_bytes) > MAX_CHUNK_LIMIT:
            until_bytes = from_bytes + MAX_CHUNK_LIMIT
    # -----------------------------------------------------------------


    # RANGE VALIDATION
    if (until_bytes > file_size) or (from_bytes < 0) or (until_bytes < from_bytes):
        return web.Response(
            status=416,
            body="416: Range not satisfiable",
            headers={"Content-Range": f"bytes */{file_size}"},
        )


    chunk_size = 1024 * 1024
    until_bytes = min(until_bytes, file_size - 1)

    offset = from_bytes - (from_bytes % chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = until_bytes % chunk_size + 1

    req_length = until_bytes - from_bytes + 1
    part_count = math.ceil(until_bytes / chunk_size) - math.floor(offset / chunk_size)
    body = tg_connect.yield_file(
        file_id, index, offset, first_part_cut, last_part_cut, part_count, chunk_size
    )

    mime_type = file_id.mime_type
    file_name = file_id.file_name
    disposition = "attachment"

    # ✅ Safe file name handling for streaming
    if not file_name:
        file_name = "file"
    elif isinstance(file_name, bytes):
        file_name = file_name.decode('utf-8', errors='ignore')
    file_name = str(file_name)

    if mime_type:
        if not file_name or file_name == "file":
            try:
                file_name = f"{secrets.token_hex(2)}.{mime_type.split('/')[1]}"
            except (IndexError, AttributeError):
                file_name = f"{secrets.token_hex(2)}.unknown"
    else:
        if file_name and file_name != "file":
            mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        else:
            mime_type = "application/octet-stream"
            file_name = f"{secrets.token_hex(2)}.unknown"

    return web.Response(
        status=206 if range_header else 200,
        body=body,
        headers={
            "Content-Type": f"{mime_type}",
            "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Content-Length": str(req_length),
            "Content-Disposition": f'{disposition}; filename="{file_name}"',
            "Accept-Ranges": "bytes",
            "Access-Control-Allow-Origin": "*",
        },
    )
