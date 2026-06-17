from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired
from google import genai
from google.genai import types
import time
import os
import config

cl = Client()

SESSION_FILE_1 = "session_bot1.json"

# Per-thread conversation history (max 20 messages rakho memory mein)
conversation_history = {}
MAX_HISTORY = 20

# Already process ho chuke message IDs — dobara process na ho
seen_message_ids = set()

# Per-user last reply time — zyada fast messages pe AI skip karo (rate limit bachao)
last_reply_time = {}
REPLY_COOLDOWN = 3  # seconds

SYSTEM_PROMPT = (
    "Tu ek friendly, funny aur smart GC (group chat) member hai Instagram pe. "
    "Tera naam 'HashBot' hai. Tu hinglish mein baat karta hai (Hindi + English mix). "
    "Chhoti, casual aur natural replies deta hai — jaise koi dost karta hai. "
    "Kabhi kabhi emojis use karta hai lekin zyada nahi. "
    "Agar koi kuch pooche toh seedha helpful jawab deta hai. "
    "Tu mature hai, bakwas ya random nahi karta. "
    "Replies always chhoti rakho — max 2-3 lines."
)

# ============================================================
# GEMINI AI SETUP
# ============================================================
gemini_client = None

def setup_gemini():
    global gemini_client
    if not config.GEMINI_API_KEY:
        print("[AI] ⚠️  GEMINI_API_KEY not set! AI chat disabled.")
        return False
    try:
        gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
        print("[AI] Gemini AI ready! ✅")
        return True
    except Exception as e:
        print(f"[AI] Gemini setup failed: {e}")
        return False

def get_ai_reply(thread_id, user_message):
    global gemini_client

    if gemini_client is None:
        print("[AI] Client not ready, skipping reply.")
        return None

    if thread_id not in conversation_history:
        conversation_history[thread_id] = []

    history = conversation_history[thread_id]

    # Build contents list from history + new message
    contents = []
    for entry in history:
        contents.append(types.Content(role=entry["role"], parts=[types.Part(text=entry["text"])]))
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

    try:
        response = gemini_client.models.generate_content(
            model="models/gemini-2.5-flash",
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            contents=contents,
        )
        reply = response.text.strip()

        # History update karo
        history.append({"role": "user", "text": user_message})
        history.append({"role": "model", "text": reply})

        # Memory limit
        if len(history) > MAX_HISTORY:
            conversation_history[thread_id] = history[-MAX_HISTORY:]

        return reply

    except Exception as e:
        err = str(e)
        print(f"[AI] Gemini error: {err[:120]}")
        # 503 = server busy, 429 = rate limit — dono pe silently skip karo, GC mein kuch mat bhejo
        if "503" in err or "429" in err or "UNAVAILABLE" in err or "RESOURCE_EXHAUSTED" in err:
            return None
        # Koi aur unexpected error — tab bhi GC mein error message mat bhejo
        return None

# ============================================================
# CHALLENGE HANDLER
# ============================================================
def challenge_code_handler_1(username, choice):
    code = os.environ.get("IG_VERIFICATION_CODE_1", "").strip()
    if code:
        print(f"[IG] Using verification code from secret IG_VERIFICATION_CODE_1")
        return code
    print(f"[IG] ⚠️  Challenge required for {username}!")
    print(f"[IG]   1. Check your email or phone for the Instagram code")
    print(f"[IG]   2. Go to Secrets and add: IG_VERIFICATION_CODE_1 = <the code>")
    print(f"[IG]   3. Restart the workflow")
    return None

cl.challenge_code_handler = challenge_code_handler_1

# ============================================================
# LOGIN
# ============================================================
def login_bot():
    if os.path.exists(SESSION_FILE_1):
        print("[IG] Session file found, loading session...")
        try:
            cl.load_settings(SESSION_FILE_1)
            cl.login(config.IG_USERNAME_1, config.IG_PASSWORD_1)
            cl.dump_settings(SESSION_FILE_1)
            print("[IG] Session loaded successfully!")
            return True
        except Exception as e:
            print(f"[IG] Session load failed ({e}), trying fresh login...")
            os.remove(SESSION_FILE_1)

    print("[IG] Attempting fresh login...")
    try:
        cl.login(config.IG_USERNAME_1, config.IG_PASSWORD_1)
        cl.dump_settings(SESSION_FILE_1)
        print("[IG] Login successful! Session saved.")
        return True
    except ChallengeRequired:
        code = os.environ.get("IG_VERIFICATION_CODE_1", "").strip()
        if not code:
            print(f"[IG] ⚠️  challenge_required — Instagram wants to verify your identity.")
            print(f"[IG]   1. Check your email or phone for the Instagram verification code")
            print(f"[IG]   2. In Replit Secrets, add: IG_VERIFICATION_CODE_1 = <your code>")
            print(f"[IG]   3. Restart the workflow")
        return False
    except Exception as e:
        print(f"[IG] Login Failed: {e}")
        return False

# ============================================================
# MAIN BOT LOOP
# ============================================================
def run_instagram_bot():
    global gemini_model
    print("[IG] Logging in to Instagram...")
    if not login_bot():
        config.STATUS["instagram_main"] = "Error 🔴 (Login Failed)"
        return

    config.STATUS["instagram_main"] = "Online 🟢"
    setup_gemini()
    print("[IG] Instagram Bot is Online!")

    while True:
        try:
            threads = cl.direct_threads(selected_filter="unread")

            for thread in threads:
                thread_id = thread.id
                messages = cl.direct_messages(thread_id, amount=1)

                if not messages:
                    continue

                last_msg = messages[0]
                msg_id = str(last_msg.id)

                # ── Dobara process mat karo ────────────────────────────────
                if msg_id in seen_message_ids:
                    continue

                if not last_msg.text:
                    seen_message_ids.add(msg_id)
                    continue

                text = last_msg.text.strip()
                text_lower = text.lower()
                sender_id = str(last_msg.user_id)

                if sender_id == str(cl.user_id):
                    seen_message_ids.add(msg_id)
                    continue

                is_owner = (sender_id == str(config.GC_OWNER_ID))

                # ── BAD WORD FILTER (sabke liye) ──────────────────────────
                if any(bad in text_lower for bad in config.BAD_WORDS):
                    print(f"[🚨] Bad word from {sender_id} in {thread_id}")
                    seen_message_ids.add(msg_id)
                    try:
                        cl.private_request(
                            f"direct_v2/threads/{thread_id}/remove_users/",
                            data={"_uuid": cl.uuid, "user_ids": f'["{sender_id}"]'},
                            with_signature=False,
                        )
                        cl.direct_send(
                            "🚫 Ek member ko gaali use karne ki wajah se remove kar diya. Tameez se baat karein!",
                            thread_ids=[thread_id]
                        )
                    except Exception as e:
                        print(f"[❌] Kick failed: {e}")
                    continue

                # ── OWNER COMMANDS (sirf owner ke liye) ───────────────────
                if is_owner and text_lower.startswith("!"):
                    cmd = text_lower.split()[0]
                    seen_message_ids.add(msg_id)

                    if cmd == "!ping":
                        cl.direct_send("Pong! 🏓", thread_ids=[thread_id])

                    elif cmd == "!status":
                        reply = (
                            f"🤖 Bot Status:\n"
                            f"📷 IG Main: {config.STATUS['instagram_main']}\n"
                            f"🛡️ Emergency: {config.STATUS['instagram_emergency']}\n"
                            f"✈️ Telegram: {config.STATUS['telegram']}\n"
                            f"🔇 Muted: {config.STATUS.get('bot_muted', False)}\n"
                            f"🧠 AI: {'On ✅' if gemini_client else 'Off ❌ (API key set karo)'}"
                        )
                        cl.direct_send(reply, thread_ids=[thread_id])

                    elif cmd == "!help":
                        reply = (
                            "🛠️ Owner Commands:\n"
                            "!ping — Bot check\n"
                            "!status — Full status\n"
                            "!warn @user — Warning do\n"
                            "!kick @user — Remove karo\n"
                            "!mute — Bot chup ho jaye\n"
                            "!unmute — Bot wapas bole\n"
                            "!reset — Is thread ki chat memory clear karo"
                        )
                        cl.direct_send(reply, thread_ids=[thread_id])

                    elif cmd == "!warn":
                        target = text[6:].strip() if len(text) > 6 else "user"
                        cl.direct_send(
                            f"⚠️ {target} — Owner ki taraf se warning! Rules follow karo.",
                            thread_ids=[thread_id]
                        )

                    elif cmd == "!mute":
                        config.STATUS["bot_muted"] = True
                        cl.direct_send("🔇 Bot muted. !unmute se wapas activate karo.", thread_ids=[thread_id])

                    elif cmd == "!unmute":
                        config.STATUS["bot_muted"] = False
                        cl.direct_send("🔊 Bot unmuted! Wapas aa gaya 😄", thread_ids=[thread_id])

                    elif cmd == "!reset":
                        conversation_history.pop(thread_id, None)
                        cl.direct_send("🧹 Is thread ki chat memory reset ho gayi!", thread_ids=[thread_id])

                    print(f"[IG] Owner command '{cmd}' used")
                    continue

                # ── AI CHAT (sirf mention ya bot-reply pe) ────────────────
                if not config.STATUS.get("bot_muted", False):

                    # Check 1: bot ka @mention text mein hai?
                    bot_mentioned = f"@{config.BOT_USERNAME}".lower() in text_lower

                    # Check 2: koi bot ke message ka reply kar raha hai?
                    bot_replied_to = False
                    try:
                        if last_msg.reply is not None:
                            replied_uid = str(last_msg.reply.user_id)
                            bot_replied_to = (replied_uid == str(cl.user_id))
                    except Exception:
                        pass

                    if not bot_mentioned and not bot_replied_to:
                        # Na mention, na reply — ignore karo
                        seen_message_ids.add(msg_id)
                        continue

                    now = time.time()
                    last_t = last_reply_time.get(sender_id, 0)
                    if now - last_t < REPLY_COOLDOWN:
                        print(f"[AI] Cooldown active for {sender_id}, skipping.")
                        seen_message_ids.add(msg_id)
                        continue

                    print(f"[AI] Generating reply for {sender_id}: {text[:40]}")
                    reply = get_ai_reply(thread_id, text)
                    if reply:
                        cl.direct_send(reply, thread_ids=[thread_id])
                        last_reply_time[sender_id] = time.time()
                        print(f"[AI] Reply sent: {reply[:60]}")

                # Message ID mark karo — chahe reply ho ya na ho
                seen_message_ids.add(msg_id)

                # Memory leak rokne ke liye purane IDs hatao (5000 se zyada ho toh)
                if len(seen_message_ids) > 5000:
                    seen_message_ids.clear()

            time.sleep(8)

        except Exception as e:
            print(f"[IG] Error occurred: {e}")
            time.sleep(15)


def send_ig_message(thread_id, text):
    try:
        cl.direct_send(text, thread_ids=[thread_id])
        return True
    except Exception as e:
        print(f"[IG] Failed to send message: {e}")
        return False
