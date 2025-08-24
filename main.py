import os
import threading
import time
from fastapi import FastAPI
import uvicorn
from pyrogram import Client, filters
import pyrogram

# Env setup
bot_token = os.environ.get("TOKEN", "") 
api_hash = os.environ.get("HASH", "") 
api_id = os.environ.get("ID", "") 
app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Make ffmpeg executable
os.system("chmod 777 ./ffmpeg/ffmpeg")

# ========== HEALTH CHECK SERVER FOR KOYEB ==========
health_app = FastAPI()

@health_app.get("/")
def read_root():
    return {"status": "ok"}

def run_health_server():
    uvicorn.run(health_app, host="0.0.0.0", port=8080)

# Start FastAPI health server in background
threading.Thread(target=run_health_server, daemon=True).start()
# =====================================================

@app.on_message(filters.command(['start']))
def echo(client, message: pyrogram.types.messages_and_media.message.Message):
    app.send_message(message.chat.id, f"**Welcome** {message.from_user.mention}\n__just send me a Video file__")


def upstatus(statusfile, message):
    while not os.path.exists(statusfile):
        time.sleep(3)
    while os.path.exists(statusfile):
        with open(statusfile, "r") as upread:
            txt = upread.read()
        try:
            app.edit_message_text(message.chat.id, message.id, f"__Uploaded__ : **{txt}**")
            time.sleep(10)
        except:
            time.sleep(5)


def downstatus(statusfile, message):
    while not os.path.exists(statusfile):
        time.sleep(3)
    while os.path.exists(statusfile):
        with open(statusfile, "r") as upread:
            txt = upread.read()
        try:
            app.edit_message_text(message.chat.id, message.id, f"__Downloaded__ : **{txt}**")
            time.sleep(10)
        except:
            time.sleep(5)


def progress(current, total, message, type):
    with open(f'{message.id}{type}status.txt', "w") as fileup:
        fileup.write(f"{current * 100 / total:.1f}%")


def compress(message, msg):
    threading.Thread(target=lambda: downstatus(f'{message.id}downstatus.txt', msg), daemon=True).start()
    vfile = app.download_media(message, progress=progress, progress_args=[message, "down"])

    if os.path.exists(f'{message.id}downstatus.txt'):
        os.remove(f'{message.id}downstatus.txt')

    name = vfile.split("/")[-1]
    output_file = f'output-{message.id}.mkv'
    cmd = f'./ffmpeg/ffmpeg -i "{vfile}" -c:v libx265 -vtag hvc1 "{output_file}"'

    app.edit_message_text(message.chat.id, msg.id, "__Compressing__")
    try:
        os.system(cmd)
    except:
        app.edit_message_text(message.chat.id, msg.id, "**Compression Error**")
        return

    if os.path.exists(output_file):
        os.remove(vfile)
    else:
        app.edit_message_text(message.chat.id, msg.id, "**Compression Failed**")
        return

    os.rename(output_file, name)
    app.edit_message_text(message.chat.id, msg.id, "__Uploading__")
    threading.Thread(target=lambda: upstatus(f'{message.id}upstatus.txt', msg), daemon=True).start()
    app.send_document(message.chat.id, document=name, force_document=True, progress=progress, progress_args=[message, "up"], reply_to_message_id=message.id)

    if os.path.exists(f'{message.id}upstatus.txt'):
        os.remove(f'{message.id}upstatus.txt')
    app.delete_messages(message.chat.id, [msg.id])
    os.remove(name)


@app.on_message(filters.document)
def document_handler(client, message):
    try:
        if "video" in message.document.mime_type:
            msg = app.send_message(message.chat.id, "__Downloading__", reply_to_message_id=message.id)
            threading.Thread(target=lambda: compress(message, msg), daemon=True).start()
    except:
        app.send_message(message.chat.id, "**Send only Videos**")


@app.on_message(filters.video)
def video_handler(client, message):
    msg = app.send_message(message.chat.id, "__Downloading__", reply_to_message_id=message.id)
    threading.Thread(target=lambda: compress(message, msg), daemon=True).start()


# Start the bot
app.run()
