import json
import os
import html
import time

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN")

COIN_COOLDOWN = 5 * 60
STEAL_COOLDOWN = 60 * 60
MAX_LEVEL = 30
COINS_PER_LEVEL = 5

DATA_FILE = "doodol_tala_data.json"


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


data = load_data()


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_group(chat_id):
    chat_id = str(chat_id)

    if chat_id not in data:
        data[chat_id] = {
            "players": {},
            "king_id": None
        }

    return data[chat_id]


def get_player(group, user):
    user_id = str(user.id)

    if user_id not in group["players"]:
        group["players"][user_id] = {
            "name": user.full_name,
            "coins": 0,
            "last_coin": 0,
            "last_steal": 0
        }

    group["players"][user_id]["name"] = user.full_name

    return group["players"][user_id]


def get_level(coins):
    return min(coins // COINS_PER_LEVEL, MAX_LEVEL)


def mention_user(user_id, name):
    return f'<a href="tg://user?id={user_id}">{html.escape(name)}</a>'


def format_time(seconds):
    seconds = max(0, int(seconds))

    minutes = seconds // 60
    seconds = seconds % 60

    if minutes > 0 and seconds > 0:
        return f"{minutes} دقیقه و {seconds} ثانیه"

    if minutes > 0:
        return f"{minutes} دقیقه"

    return f"{seconds} ثانیه"


async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = update.my_chat_member

    if not member:
        return

    if member.new_chat_member.status == "member":
        await update.effective_chat.send_message(
            """سلامممم ›_‹

ممنون که منو به گپ اضاف کردی🤓🫶
اینجا قراره کلی دودول طلا جمع کنی و با بقیه رقابت کنی😝
فقط کافیه هر ۵ دقیقه بگی «دودول طلا»، سطحتو ببری بالا و آخرش بشی شاه شهر دودول طلاییان👑

اگه متوجه نشدی بگو راهنما😝
ببینیم کی زودتر به سطح ۳۰ می‌رسه 😼"""
        )


async def game_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user = update.effective_user
    chat = update.effective_chat

    if not user or not chat:
        return

    group = get_group(chat.id)
    player = get_player(group, user)

    if text == "راهنما":
        await update.message.reply_text(
            """📖 راهنمای بازی دودول طلاییان ›_‹

😼 هر ۵ دقیقه یک بار بگو «دودول طلا» تا دودول طلایت طلایی‌تر بشه!

⬆️ هر ۵ بار گفتن «دودول طلا» = یک سطح بالاتر
🏆 بازی ۳۰ سطح داره.

👑 هرکس زودتر به سطح ۳۰ برسه، شاه شهر دودول طلاییان میشه!

🕵️ شاه هر ۱ ساعت یک بار می‌تونه دزدی کنه.
کافیه روی پیام یکی از بازیکن‌ها ریپلای کنه و بنویسه «دزدی» تا یک سطح از اون شخص کم بشه.

😼 برای دیدن سطح خودت بگو «سطح من»
🏆 برای دیدن رتبه‌بندی شهر بگو «سطح شهر»

حالا برو دودول طلا جمع کن و ببینیم کی شاه میشه 😼👑"""
        )
        return

    if text == "سطح من":
        level = get_level(player["coins"])

        await update.message 
