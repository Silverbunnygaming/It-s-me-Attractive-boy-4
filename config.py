import os

# Bot 1 (Main Bot - Jo normal kaam karega)
IG_USERNAME_1 = os.environ.get('IG_USERNAME_1')
IG_PASSWORD_1 = os.environ.get('IG_PASSWORD_1')

# Bot 2 (Emergency Bot - Jo sirf security dekhega)
IG_USERNAME_2 = os.environ.get('IG_USERNAME_2')
IG_PASSWORD_2 = os.environ.get('IG_PASSWORD_2')

# Telegram Config
TG_TOKEN = os.environ.get('TG_TOKEN')
TG_ADMIN_ID = os.environ.get('TG_ADMIN_ID')

# Target Group Chat ID (Jise secure karna hai)
TARGET_GC_ID = os.environ.get('TARGET_GC_ID')

# GC Owner ka Instagram User ID (Sirf yahi commands de sakta hai)
GC_OWNER_ID = "49573475777"

# Main bot ka Instagram username (mention detect karne ke liye)
BOT_USERNAME = "its_me_attractive_boy4"

# Gemini AI API Key
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

STATUS = {"instagram_main": "Offline", "instagram_emergency": "Offline", "telegram": "Offline", "bot_muted": False}

# Bad words ki list (Sab lowercase me likhna)
BAD_WORDS = [
    "abuse1", 
    "abuse2", 
    "gali1", 
    "gali2",
    "bhosdk",
    "madarchod",
    "chut"
    "maki"
    "gand"
    "bhadwe"
    "bhenchod"
    "bhadwa"
    "bhadva"
    "bhosdike"
    "chod"
    # Yahan jo bhi words block karne hain, comma lagakar double quotes me likhte jao
]
