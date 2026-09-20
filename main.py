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

        await update.message.reply_text(
            f"""سطح تو:: {level}/30

دودول طلایت {player["coins"]} درصد طلایی شده!😼"""
        )
        return

    if text == "سطح شهر":
        players = group["players"]

        ranking = sorted(
            players.items(),
            key=lambda item: (
                get_level(item[1]["coins"]),
                item[1]["coins"]
            ),
            reverse=True
        )

        if not ranking:
            await update.message.reply_text(
                "هنوز کسی دودول طلا جمع نکرده😼"
            )
            return

        lines = []

        for user_id, p in ranking:
            level = get_level(p["coins"])

            lines.append(
                f'{mention_user(user_id, p["name"])} {level}/30'
            )

        await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.HTML
        )
        return

    if text == "دودول طلا":
        now = time.time()
        remaining = COIN_COOLDOWN - (now - player["last_coin"])

        if remaining > 0:
            await update.message.reply_text(
                f"""عیبابا داری عجله میکنیا!!

هنوز {format_time(remaining)} مونده😼."""
            )
            return

        if get_level(player["coins"]) >= MAX_LEVEL:
            await update.message.reply_text(
                "تو الان سطح ۳۰ هستی😼👑"
            )
            return

        player["coins"] += 1
        player["last_coin"] = now

        new_level = get_level(player["coins"])

        if new_level >= MAX_LEVEL:
            old_king = group["king_id"]

            if old_king and old_king != str(user.id):
                if old_king in group["players"]:
                    group["players"][old_king]["coins"] = 0

            group["king_id"] = str(user.id)

            save_data()

            await update.message.reply_text(
                """عررررر😭

شاه شهر دودول طلاییان شدی😝

حالا وقت رقابته!!
اگه کسی سطحش برسه به تو اون شاه میشه و تو دوباره باید از صفر شروع کنی😼"""
            )
            return

        if player["coins"] % COINS_PER_LEVEL == 0:
            await update.message.reply_text(
                f"""هورااااا😝 به سطح {new_level} رسیدی ›_‹

تبریک میگم یه سطح بالا رفتی😼
سطح الانت:: {new_level}/30"""
            )
        else:
            await update.message.reply_text(
                """دودولت طلایی شد😼
یادت نره با هر پنج بار دودول طلا گفتن یک سطح میری بالاتر!"""
            )

        save_data()
        return

    if text == "دزدی":
        king_id = group["king_id"]

        if str(user.id) != king_id:
            await update.message.reply_text(
                """فقط شاه شهر میتونه دزدی کنه😾!!

تو هم وقتی شاه شدی میتونی دزدی کنی😼
البته اگه شاه شهر فعلی باهات رقابت نکنه😹"""
            )
            return

        if not update.message.reply_to_message:
            await update.message.reply_text(
                "برای دزدی باید روی پیام یکی از بازیکن‌ها ریپلای کنی😼"
            )
            return

        target = update.message.reply_to_message.from_user

        if not target:
            return

        if target.id == user.id:
            await update.message.reply_text(
                """دیوونه شدی؟ نمیتونی که از خودت دزدی کنی!!

نکنه میخوای از سطح خودت کم کنی و دیگه شاه نباشی؟😾"""
            )
            return

        now = time.time()
        remaining = STEAL_COOLDOWN - (now - player["last_steal"])

        if remaining > 0:
            await update.message.reply_text(
                f"هیییی صبر کننن هنوز {format_time(remaining)} دیگه مونده😾"
            )
            return

        target_player = get_player(group, target)
        target_level = get_level(target_player["coins"])

        if target_level <= 0:
            await update.message.reply_text(
                """عاخخخ

کسی که روش ریپلای کردی هنوز سطحی نداره😾"""
            )
            return

        target_player["coins"] -= COINS_PER_LEVEL
        player["last_steal"] = now

        save_data()

        target_mention = mention_user(
            str(target.id),
            target.full_name
        )

        await update.message.reply_text(
            f"یک سطح از {target_mention} توسط شاه شهر دودول طلاییان دزدیده شد😼",
            parse_mode=ParseMode.HTML
        )
        return


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


app = Application.builder().token(TOKEN).build()

app.add_handler(
    ChatMemberHandler(
        welcome,
        ChatMemberHandler.MY_CHAT_MEMBER
    )
)

app.add_handler(
    CommandHandler("help", help_command)
)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        game_message
    )
)

print("ربات روشن شد 🪙👑")

app.run_polling()
