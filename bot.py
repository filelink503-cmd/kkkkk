# Don't Remove Credit @BabuBhaiKundan

import sys, glob, importlib, logging, logging.config, pytz, asyncio
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import date, datetime
from aiohttp import web

# Logging configuration
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)

from pyrogram import idle
from database.users_chats_db import db
from info import *
from utils import temp
from Script import script
from plugins import web_server

from BabuBhaiKundan.bot import BabuBhaiKundanBot
from BabuBhaiKundan.util.keepalive import ping_server
from BabuBhaiKundan.bot.clients import initialize_clients

ppath = "plugins/*.py"
files = glob.glob(ppath)

# ------------------------------------------------
# ORIGINAL FLOW (Important - change mat karna)
BabuBhaiKundanBot.start()
loop = asyncio.get_event_loop()
# ------------------------------------------------


async def start():
    print("\n🚀 Initializing Your Bot...\n")

    bot_info = await BabuBhaiKundanBot.get_me()

    await initialize_clients()
    
    # Plugin ko comment karo because bot ko command nhi dena hai
    '''
    # Plugin Loader
    for name in files:
        with open(name) as a:

            patt = Path(a.name)
            plugin_name = patt.stem.replace(".py", "")

            # skip __init__
            if plugin_name == "__init__":
                continue

            plugins_dir = Path(f"plugins/{plugin_name}.py")
            import_path = f"plugins.{plugin_name}"

            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
            load = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(load)

            sys.modules[import_path] = load
            print("✅️ Imported Plugin =>", plugin_name)
    '''


    if ON_HEROKU:
        asyncio.create_task(ping_server())

    me = await BabuBhaiKundanBot.get_me()

    temp.BOT = BabuBhaiKundanBot
    temp.ME = me.id
    temp.U_NAME = me.username
    temp.B_NAME = me.first_name

    tz = pytz.timezone("Asia/Kolkata")
    today = date.today()
    now = datetime.now(tz)
    time_now = now.strftime("%H:%M:%S %p")

    await BabuBhaiKundanBot.send_message(
        chat_id=LOG_CHANNEL,
        text=script.RESTART_TXT.format(today, time_now)
    )

    # Web Server
    app = web.AppRunner(await web_server())
    await app.setup()

    bind_address = "0.0.0.0"

    # Railway safe port
    await web.TCPSite(app, bind_address, int(PORT)).start()

    print(f"🌐 Web Server Started on {bind_address}:{PORT}")

    await idle()


if __name__ == "__main__":
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logging.info("Service Stopped Bye 👋")