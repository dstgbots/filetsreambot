#(c) NobiDeveloper
import os
import asyncio
import logging
from asyncio import TimeoutError
from Adarsh.bot import StreamBot
from Adarsh.utils.database import Database
from Adarsh.utils.human_readable import humanbytes
from Adarsh.vars import Var
from urllib.parse import quote_plus
from pyrogram import filters, Client
from pyrogram.errors import FloodWait, UserNotParticipant
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from Adarsh.utils.file_properties import get_name, get_hash, get_media_file_size
db = Database(Var.DATABASE_URL, Var.name)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


MY_PASS = os.environ.get("MY_PASS", None)
pass_dict = {}
pass_db = Database(Var.DATABASE_URL, "ag_passwords")


@StreamBot.on_message((filters.regex("login🔑") | filters.command("login")) , group=4)
async def login_handler(c: Client, m: Message):
    try:
        try:
            ag = await m.reply_text("Now send me password.\n\n If You don't know check the MY_PASS Variable in heroku \n\n(You can use /cancel command to cancel the process)")
            _text = await c.listen(m.chat.id, filters=filters.text, timeout=90)
            if _text.text:
                textp = _text.text
                if textp == "/cancel":
                   await ag.edit("Process Cancelled Successfully")
                   return
            else:
                return
        except TimeoutError:
            await ag.edit("I can't wait more for password, try again")
            return
        if textp == MY_PASS:
            await pass_db.add_user_pass(m.chat.id, textp)
            ag_text = "yeah! you entered the password correctly"
        else:
            ag_text = "Wrong password, try again"
        await ag.edit(ag_text)
    except Exception as e:
        print(e)

@StreamBot.on_message((filters.private) & (filters.document | filters.video | filters.audio | filters.photo), group=4)
async def private_receive_handler(c: Client, m: Message):
    try:
        # Check for password if enabled
        if MY_PASS:
            check_pass = await pass_db.get_user_pass(m.chat.id)
            if check_pass is None:
                await m.reply_text("Login first using /login cmd \ndon't know the pass? request it from the Developer")
                return
            if check_pass != MY_PASS:
                await pass_db.delete_user(m.chat.id)
                return

        # Add new user to database
        if not await db.is_user_exist(m.from_user.id):
            await db.add_user(m.from_user.id)
            try:
                await c.send_message(
                    Var.BIN_CHANNEL,
                    f"New User Joined! : \n\n Name : [{m.from_user.first_name}](tg://user?id={m.from_user.id}) Started Your Bot!!"
                )
            except Exception as e:
                logging.error(f"Failed to send new user notification: {str(e)}")

        # Updates channel check
        if Var.UPDATES_CHANNEL != "None":
            try:
                # Try to get chat member first to establish peer connection
                user = await c.get_chat_member(Var.UPDATES_CHANNEL, m.chat.id)
                if user.status == "kicked":
                    await c.send_message(
                        chat_id=m.chat.id,
                        text="You are banned!\n\n  **Contact Developer [Nobita](https://telegram.me/NobiDeveloperSupport) he will help you.**",
                        disable_web_page_preview=True
                    )
                    return
            except UserNotParticipant:
                await c.send_message(
                    chat_id=m.chat.id,
                    text="<b>ᴊᴏɪɴ ᴏᴜʀ ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜꜱᴇ ᴍᴇ</b>",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⛔  ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ  ⛔", url=f"https://telegram.me/{Var.UPDATES_CHANNEL}")]
                    ])
                )
                return
            except Exception as e:
                logging.error(f"Updates channel check error: {str(e)}")
                await m.reply_text(
                    "**sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ. ᴄᴏɴᴛᴀᴄᴛ ᴍʏ [ʙᴏss](https://telegram.me/NobiDeveloperr)**",
                    disable_web_page_preview=True
                )
                return

        # Initialize connection with BIN_CHANNEL
        try:
            await c.get_chat(Var.BIN_CHANNEL)
        except Exception as e:
            logging.error(f"Failed to initialize BIN_CHANNEL: {str(e)}")
            await m.reply_text("Server connection error. Please try again later.")
            return

        # Forward file and generate links
        try:
            log_msg = await m.forward(chat_id=Var.BIN_CHANNEL)
            
            stream_link = f"{Var.URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
            online_link = f"{Var.URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"

            msg_text = """
<b>ʏᴏᴜʀ ʟɪɴᴋ ɪs ɢᴇɴᴇʀᴀᴛᴇᴅ...⚡</b>
<b>📧 ꜰɪʟᴇ ɴᴀᴍᴇ :- </b> <i>{}</i>
<b>📦 ꜰɪʟᴇ sɪᴢᴇ :- </b> <i>{}</i>
<b>⚠️ ᴛʜɪꜱ ʟɪɴᴋ ᴡɪʟʟ ᴇxᴘɪʀᴇ ᴀꜰᴛᴇʀ 𝟸𝟺 ʜᴏᴜʀꜱ</b>
<b>❇️  ᴍᴀɪɴᴛᴀɪɴᴇᴅ ʙʏ : @MovievillaYT</b>"""

            # Send notification to log channel
            await log_msg.reply_text(
                text=f"**ʀᴇǫᴜᴇꜱᴛᴇᴅ ʙʏ :** [{m.from_user.first_name}](tg://user?id={m.from_user.id})\n"
                     f"**Uꜱᴇʀ ɪᴅ :** `{m.from_user.id}`\n"
                     f"**Stream ʟɪɴᴋ :** {stream_link}",
                disable_web_page_preview=True,
                quote=True
            )

            # Send response to user
            await m.reply_text(
                text=msg_text.format(get_name(log_msg), humanbytes(get_media_file_size(m))),
                quote=True,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🖥️  ꜱᴛʀᴇᴀᴍ  🖥️", url=stream_link),
                     InlineKeyboardButton('📥  ᴅᴏᴡɴʟᴏᴀᴅ  📥', url=online_link)],
                    [InlineKeyboardButton('🎪  ꜱᴜʙꜱᴄʀɪʙᴇ ᴍʏ ʏᴛ ᴄʜᴀɴɴᴇʟ  🎪', 
                                        url='https://youtube.com/@NobiDeveloper')]
                ])
            )

        except FloodWait as e:
            logging.warning(f"FloodWait: {str(e.x)}s")
            await asyncio.sleep(e.x)
            await c.send_message(
                chat_id=Var.BIN_CHANNEL,
                text=f"Gᴏᴛ FʟᴏᴏᴅWᴀɪᴛ ᴏғ {str(e.x)}s from [{m.from_user.first_name}](tg://user?id={m.from_user.id})\n\n"
                     f"**𝚄𝚜𝚎𝚛 𝙸𝙳 :** `{str(m.from_user.id)}`",
                disable_web_page_preview=True
            )
        except Exception as e:
            logging.error(f"Failed to process file: {str(e)}")
            await m.reply_text("Failed to process your file. Please try again later.")

    except Exception as main_error:
        logging.error(f"Main handler error: {str(main_error)}")
        await m.reply_text("An unexpected error occurred. Please try again later.")


@StreamBot.on_message(filters.channel & ~filters.group & (filters.document | filters.video | filters.photo)  & ~filters.forwarded, group=-1)
async def channel_receive_handler(bot, broadcast):
    if MY_PASS:
        check_pass = await pass_db.get_user_pass(broadcast.chat.id)
        if check_pass == None:
            await broadcast.reply_text("Login first using /login cmd \n don\'t know the pass? request it from developer!")
            return
        if check_pass != MY_PASS:
            await broadcast.reply_text("Wrong password, login again")
            await pass_db.delete_user(broadcast.chat.id)
            
            return
    if int(broadcast.chat.id) in Var.BANNED_CHANNELS:
        await bot.leave_chat(broadcast.chat.id)
        
        return
    try:
        log_msg = await broadcast.forward(chat_id=Var.BIN_CHANNEL)
        stream_link = f"{Var.URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
        online_link = f"{Var.URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
        await log_msg.reply_text(
            text=f"**Channel Name:** `{broadcast.chat.title}`\n**CHANNEL ID:** `{broadcast.chat.id}`\n**ʀᴇǫᴜᴇꜱᴛ ᴜʀʟ:** {stream_link}",
            quote=True
        )
        await bot.edit_message_reply_markup(
            chat_id=broadcast.chat.id,
            message_id=broadcast.id,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🖥️  ꜱᴛʀᴇᴀᴍ  🖥️", url=stream_link),
                     InlineKeyboardButton('📥  ᴅᴏᴡɴʟᴏᴀᴅ  📥', url=online_link)],
                    [InlineKeyboardButton('🎪  ꜱᴜʙꜱᴄʀɪʙᴇ ᴍʏ ʏᴛ ᴄʜᴀɴɴᴇʟ  🎪', url='https://youtube.com/@NobiDeveloper')]
                ]
            )
        )
    except FloodWait as w:
        print(f"Sleeping for {str(w.x)}s")
        await asyncio.sleep(w.x)
        await bot.send_message(chat_id=Var.BIN_CHANNEL,
                             text=f"GOT FLOODWAIT OF {str(w.x)}s FROM {broadcast.chat.title}\n\n**CHANNEL ID:** `{str(broadcast.chat.id)}`",
                             disable_web_page_preview=True)
    except Exception as e:
        await bot.send_message(chat_id=Var.BIN_CHANNEL, text=f"**#ERROR_TRACKEBACK:** `{e}`", disable_web_page_preview=True)
        print(f"Cᴀɴ'ᴛ Eᴅɪᴛ Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ!\nEʀʀᴏʀ:  **Give me edit permission in updates and bin Channel!{e}**")
