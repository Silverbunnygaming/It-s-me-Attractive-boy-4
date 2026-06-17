from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired
import telebot
import time
import os
import config

cl2 = Client()

SESSION_FILE_2 = "session_bot2.json"

def challenge_code_handler_2(username, choice):
    code = os.environ.get("IG_VERIFICATION_CODE_2", "").strip()
    if code:
        print(f"[EMERGENCY] Using verification code from secret IG_VERIFICATION_CODE_2")
        return code
    print(f"[EMERGENCY] ⚠️  Challenge required for {username}!")
    print(f"[EMERGENCY]   1. Check your email or phone for the Instagram code")
    print(f"[EMERGENCY]   2. Go to Secrets and add: IG_VERIFICATION_CODE_2 = <the code>")
    print(f"[EMERGENCY]   3. Restart the workflow")
    return None

cl2.challenge_code_handler = challenge_code_handler_2

def send_tg_alert(text):
    try:
        if config.TG_TOKEN and config.TG_ADMIN_ID:
            tg = telebot.TeleBot(config.TG_TOKEN)
            tg.send_message(config.TG_ADMIN_ID, text)
    except Exception as e:
        print(f"[EMERGENCY] TG alert failed: {e}")

def login_emergency_bot():
    if os.path.exists(SESSION_FILE_2):
        print("[EMERGENCY] Session file found, loading session...")
        try:
            cl2.load_settings(SESSION_FILE_2)
            cl2.login(config.IG_USERNAME_2, config.IG_PASSWORD_2)
            cl2.dump_settings(SESSION_FILE_2)
            print("[EMERGENCY] Session loaded successfully!")
            return True
        except Exception as e:
            print(f"[EMERGENCY] Session load failed ({e}), trying fresh login...")
            os.remove(SESSION_FILE_2)

    print("[EMERGENCY] Attempting fresh login...")
    try:
        cl2.login(config.IG_USERNAME_2, config.IG_PASSWORD_2)
        cl2.dump_settings(SESSION_FILE_2)
        print("[EMERGENCY] Login successful! Session saved.")
        return True
    except ChallengeRequired:
        code = os.environ.get("IG_VERIFICATION_CODE_2", "").strip()
        if not code:
            print(f"[EMERGENCY] ⚠️  challenge_required — Instagram wants to verify your identity.")
            print(f"[EMERGENCY]   1. Check your email or phone for the Instagram verification code")
            print(f"[EMERGENCY]   2. In Replit Secrets, add: IG_VERIFICATION_CODE_2 = <your code>")
            print(f"[EMERGENCY]   3. Restart the workflow")
        return False
    except Exception as e:
        print(f"[EMERGENCY] Login Failed: {e}")
        return False

def run_emergency_bot():
    print("[EMERGENCY] Logging in Emergency Bot...")
    if not login_emergency_bot():
        config.STATUS["instagram_emergency"] = "Error 🔴"
        return

    config.STATUS["instagram_emergency"] = "Monitoring 🛡️"
    print("[EMERGENCY] Emergency Bot is Online and Guarding!")

    main_bot_id = None
    for attempt in range(5):
        try:
            main_bot_id = cl2.user_id_from_username(config.IG_USERNAME_1)
            print(f"[EMERGENCY] Main Bot ID fetched: {main_bot_id}")
            break
        except Exception as e:
            wait = 60 * (attempt + 1)
            print(f"[EMERGENCY] Could not fetch Main Bot ID (attempt {attempt+1}/5): {e}")
            print(f"[EMERGENCY] Retrying in {wait} seconds...")
            time.sleep(wait)

    if not main_bot_id:
        print("[EMERGENCY] Failed to fetch Main Bot ID after 5 attempts. Exiting.")
        return

    gc_id = config.TARGET_GC_ID
    if not gc_id or len(str(gc_id)) < 10:
        print(f"[EMERGENCY] ❌ TARGET_GC_ID '{gc_id}' galat lag raha hai!")
        print(f"[EMERGENCY] Instagram thread ID bahut lamba hota hai (18-19 digits), jaise:")
        print(f"[EMERGENCY]   340282366841510300949128268610842297468")
        print(f"[EMERGENCY] Sahi ID kaise nikaalein:")
        print(f"[EMERGENCY]   1. Instagram app mein apna GC open karo")
        print(f"[EMERGENCY]   2. Kisi message pe tap karo → 'Copy Link'")
        print(f"[EMERGENCY]   3. Link se lamba number copy karo")
        print(f"[EMERGENCY]   4. Secrets mein TARGET_GC_ID update karo aur restart karo")
        return

    while True:
        try:
            thread = cl2.direct_thread(int(gc_id))
            current_admins = thread.admin_user_ids

            if str(main_bot_id) not in [str(x) for x in current_admins]:
                print("[🚨 LOCKDOWN 🚨] MAIN BOT ADMIN SE HATA DIYA GAYA! SUSPICIOUS ADMINS REMOVE HO RAHE HAIN...")

                # Sabse pehle Telegram alert bhejo
                send_tg_alert(
                    "🚨 LOCKDOWN ACTIVATED 🚨\n\n"
                    "Main Bot ko GC mein admin se hata diya gaya!\n"
                    "Suspicious admins ko group se remove kiya ja raha hai...\n\n"
                    f"GC ID: {gc_id}"
                )

                # Sirf suspicious admins ko remove karo
                # (jo na main bot hain, na emergency bot)
                removed = []
                failed = []
                for admin_id in current_admins:
                    if str(admin_id) == str(cl2.user_id):
                        continue
                    if str(admin_id) == str(main_bot_id):
                        continue
                    try:
                        cl2.private_request(
                            f"direct_v2/threads/{gc_id}/remove_users/",
                            data={
                                "_uuid": cl2.uuid,
                                "user_ids": f'["{admin_id}"]'
                            },
                            with_signature=False,
                        )
                        removed.append(str(admin_id))
                        print(f"[🛡️] Removed suspicious admin: {admin_id}")
                    except Exception as err:
                        failed.append(str(admin_id))
                        print(f"[❌] Failed to remove {admin_id}: {err}")

                # GC mein warning message bhejo
                try:
                    cl2.direct_send(
                        "🔒 SECURITY LOCKDOWN 🔒\nMain bot ko admin se hatane ki koshish detect hui. Suspicious admins ko remove kar diya gaya. GC owner se sampark karein.",
                        thread_ids=[gc_id]
                    )
                except Exception:
                    pass

                print(f"[🛡️] Lockdown complete. Removed: {len(removed)}, Failed: {len(failed)}")
                send_tg_alert(
                    f"✅ Lockdown complete!\n"
                    f"Removed: {len(removed)} suspicious admins\n"
                    f"Failed: {len(failed)}\n\n"
                    f"Ab main bot ko wapas admin banao."
                )
                time.sleep(300)

            time.sleep(7)

        except Exception as e:
            print(f"[EMERGENCY ERROR]: {e}")
            time.sleep(15)
