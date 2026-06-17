import threading
import config
from instagram_bot import run_instagram_bot
from emergency_bot import run_emergency_bot
from telegram_bot import run_telegram_bot

if __name__ == "__main__":
    print("🚀 Starting Advanced Multi-Bot Security System...")

    # Threads Create Karna
    ig_main_thread = threading.Thread(target=run_instagram_bot)
    ig_emergency_thread = threading.Thread(target=run_emergency_bot)
    tg_thread = threading.Thread(target=run_telegram_bot)

    # Threads Start Karna
    ig_main_thread.start()
    ig_emergency_thread.start()
    tg_thread.start()

    # Merge threads
    ig_main_thread.join()
    ig_emergency_thread.join()
    tg_thread.join()
    