import os
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from telethon import TelegramClient, events
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telethon.tl.custom.message import Message

# --- Завантажуємо тільки API ключі з .env ---
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "assistant_session")

# --- Ім'я файлу сесії ---
session_file = f"{SESSION_NAME}.session"
if not os.path.exists(session_file):
    print(f"❌ Session файл {session_file} не знайдено. Використовуй start.sh для створення SESSION_B64.")
    exit(1)

# --- Створюємо клієнта та планувальник ---
client = TelegramClient(session_file, API_ID, API_HASH)
scheduler = AsyncIOScheduler(timezone=ZoneInfo("Europe/Kyiv"))

# --- Форматування дати для звітів ---
def format_dt(dt: datetime) -> str:
    return dt.strftime("**%Y-%m-%d-%H-%M**")

# --- Відправка повідомлень ---
async def send_to_users(usernames, message_obj: Message, run_dt):
    log = []
    success = 0

    # Беремо лише тіло повідомлення до ####
    message_cut = message_obj.message.split("####")[0].strip()
    message_obj.message = message_cut

    for uname in usernames:
        try:
            entity = await client.get_entity(uname.lstrip("@"))
            await client.send_message(entity, message_obj)
            log.append(f"✅ {uname}")
            success += 1
            await asyncio.sleep(1)
        except Exception as e:
            log.append(f"❌ {uname}: {e}")

    # Звіт про доставку
    summary = (
        f"📋 Відправлено **{success}/{len(usernames)}** повідомлень з {format_dt(run_dt)}:\n"
        + "\n".join(log)
    )
    await client.send_message("me", summary, parse_mode="markdown")

# --- Обробка нових повідомлень ---
@client.on(events.NewMessage(chats="me"))
async def handler(event):
    parts = event.raw_text.split("####")
    if len(parts) < 3:
        return

    users = [u.strip() for u in parts[1].split() if u.strip()]
    time_block = parts[2].strip()

    try:
        run_dt = datetime.strptime(time_block, "%Y-%m-%d-%H-%M").replace(tzinfo=ZoneInfo("Europe/Kyiv"))
    except ValueError:
        await client.send_message("me", "❌ Невірний формат часу. Використай YYYY-MM-DD-HH-MM.")
        return

    # Планування розсилки
    scheduler.add_job(send_to_users, "date", run_date=run_dt, args=[users, event.message, run_dt])
    await client.send_message(
        "me",
        f"⏰ Заплановано **{len(users)}** повідомлень на {format_dt(run_dt)}",
        parse_mode="markdown"
    )

# --- Головна функція ---
async def main():
    await client.start()
    scheduler.start()
    print("Помічник запущено. Чекаю інструкцій у Saved Messages...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
