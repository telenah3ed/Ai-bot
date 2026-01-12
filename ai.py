import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
import requests
import urllib.parse
import json
import os
import logging

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===============================
# 🔐 BOT CONFIGURATION
# ===============================
BOT_TOKEN = "8503553442:AAFaxWysqaN49_7ZGhWhUEMOa6p6LJ577-A"  # আপনার বট টোকেন
PRIVATE_CHANNEL_ID = -1003393383836  # প্রাইভেট চ্যানেল আইডি
PUBLIC_CHANNEL_ID = "@ainah3ed"  # পাবলিক চ্যানেল ইউজারনেম (e.g., @channel)
PRIVATE_INVITE = "https://t.me/+IbAbucfcAwlmMzE1"
PUBLIC_LINK = "https://t.me/ainah3ed"
ADMIN_IDS = [8269166427]  # আপনার অ্যাডমিন আইডি

# --- Developer & Powered by Links ---
DEVELOPER_USERNAME = "nah3ed"  # Developer's username without @
POWERED_BY_LINK = "https://t.me/ainah3ed"

USERS_FILE = "csb_users_db.json"
DEFAULT_CREDITS = 100  # নতুন ইউজারকে ডিফল্ট কত ক্রেডিট দেওয়া হবে

# ===============================
# ⚙️ USER DATABASE (উন্নত)
# ===============================

def load_users():
    """ইউজার ডেটাবেস লোড করে (JSON ডিকশনারি)"""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_users(users_data):
    """ইউজার ডেটাবেস সেভ করে"""
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f, indent=4)

def get_user_data(user_id, first_name):
    """ইউজারের ডেটা আনে বা নতুন ইউজার তৈরি করে"""
    users = load_users()
    user_id_str = str(user_id)  # JSON-এ key সবসময় string হয়

    if user_id_str not in users:
        users[user_id_str] = {
            "first_name": first_name,
            "credits": DEFAULT_CREDITS,
            "images_generated": 0,
            "videos_generated": 0,
            "is_verified": False # ভেরিফিকেশন স্ট্যাটাস
        }
        save_users(users)
    
    # যদি ইউজার আগে ভেরিফাই না করে থাকে, তবে স্ট্যাটাস আপডেট করি
    if "is_verified" not in users[user_id_str]:
        users[user_id_str]["is_verified"] = False
        save_users(users)

    return users[user_id_str]

def update_user_credits(user_id, amount):
    """ইউজারের ক্রেডিট আপডেট করে (amount পজিটিভ বা নেগেটিভ হতে পারে)"""
    users = load_users()
    user_id_str = str(user_id)
    if user_id_str in users:
        users[user_id_str]["credits"] += amount
        save_users(users)
        return users[user_id_str]["credits"]
    return 0

def set_user_credits(user_id, total_amount):
    """ইউজারের মোট ক্রেডিট সেট করে (অ্যাডমিন প্যানেলের জন্য)"""
    users = load_users()
    user_id_str = str(user_id)
    if user_id_str not in users:
        # যদি ইউজার ডেটাবেসেই না থাকে (সম্ভাবনা কম)
        users[user_id_str] = {
            "first_name": "N/A (Admin Added)",
            "credits": total_amount,
            "images_generated": 0,
            "videos_generated": 0,
            "is_verified": False
        }
    else:
        users[user_id_str]["credits"] = total_amount
    save_users(users)
    return True

def increment_user_stat(user_id, stat_type):
    """ইউজারের স্ট্যাটাস (ইমেজ/ভিডিও সংখ্যা) বাড়ায়"""
    users = load_users()
    user_id_str = str(user_id)
    if user_id_str in users:
        if stat_type == "image":
            users[user_id_str]["images_generated"] += 1
        elif stat_type == "video":
            users[user_id_str]["videos_generated"] += 1
        save_users(users)

def set_user_verified(user_id, status=True):
    """ইউজারের ভেরিফিকেশন স্ট্যাটাস সেভ করে"""
    users = load_users()
    user_id_str = str(user_id)
    if user_id_str in users:
        users[user_id_str]["is_verified"] = status
        save_users(users)

# ===============================
# 🚀 /start Command
# ===============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    # ইউজারকে ডেটাবেসে রেজিস্টার বা ডেটা আনা হয়
    user_data = get_user_data(user.id, user.first_name)

    # যদি ইউজার অলরেডি ভেরিফাইড হয়, তাহলে মেইন মেনু দেখাবে
    if user_data.get("is_verified", False):
        await show_main_menu(update, context)
        return

    # ভেরিফাইড না হলে, ভেরিফিকেশন প্রসেস
    keyboard = [[InlineKeyboardButton("✅ CSB VERIFY", callback_data="verify")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = f"""
👋 Welcome {user.first_name}!

🔹 This is CSB AI BOT — powered by Cyber Sentinel Bangladesh 🛡️

To access all features, please join our official channels first:

1️⃣ <a href="{PUBLIC_LINK}"><b>Join CSB Public Channel</b></a>
2️⃣ <a href="{PRIVATE_INVITE}"><b>Join CSB Private Channel</b></a>

Then click the ✅ <b>CSB VERIFY</b> button below to continue.
"""
    await update.message.reply_html(welcome_text, reply_markup=reply_markup, disable_web_page_preview=True)

# ===============================
# MainMenu & Profile (আপডেটেড)
# ===============================

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ইউজারকে প্রধান মেনু দেখায় (ফুটার সহ)"""
    keyboard = [
        [InlineKeyboardButton("🖼️ Generate Image", callback_data="gen_image")],
        [InlineKeyboardButton("🎬 Generate Video", callback_data="gen_video")],
        [InlineKeyboardButton("👤 My Profile", callback_data="my_profile")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    menu_text = f"""
✅ **Verification Successful!**

Welcome to the CSB AI BOT main menu. Choose an option to start.

━━━━━━━━━━━━━━━
<b>🔧 Powered by:</b> <a href="{POWERED_BY_LINK}">Cyber Sentinel Bangladesh</a>
<b>👨‍💻 Developer:</b> <a href="https://t.me/{DEVELOPER_USERNAME}">BIJOY (CSB)</a>
"""

    # যদি এটি /start থেকে আসে (update.message আছে)
    if update.message:
        await update.message.reply_html(menu_text, reply_markup=reply_markup, disable_web_page_preview=True)
    # যদি এটি callback query থেকে আসে (e.g., 'Back' button)
    elif update.callback_query:
        query = update.callback_query
        try:
            await query.message.edit_text(menu_text, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
        except telegram.error.BadRequest as e:
            if "message is not modified" not in str(e):
                logger.error(f"Error editing message: {e}")
            await query.answer() # বাটন ক্লিক হয়েছে, সেটা ইউজারকে জানাই
    else:
        # এটি হতে পারে কোনো জেনারেশনের পর বা /cancel থেকে
        chat_id = update.effective_chat.id
        await context.bot.send_message(chat_id, menu_text, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)


async def show_profile(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE):
    """ইউজারের প্রোফাইল দেখায়"""
    user = query.from_user
    user_data = get_user_data(user.id, user.first_name) # লেটেস্ট ডেটা লোড করি

    profile_text = f"""
👤 **CSB AI Profile**

**Name:** {user.first_name}
**User ID:** `{user.id}`
**Credits:** {user_data['credits']} 🪙

**Total Images Generated:** {user_data['images_generated']} 🖼️
**Total Videos Generated:** {user_data['videos_generated']} 🎬
"""
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(profile_text, reply_markup=reply_markup, parse_mode="Markdown")

# ===============================
# ✅ VERIFY BUTTON HANDLER
# ===============================

async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user

    try:
        # প্রাইভেট এবং পাবলিক চ্যানেলের মেম্বারশিপ চেক
        private_member = await context.bot.get_chat_member(PRIVATE_CHANNEL_ID, user.id)
        public_member = await context.bot.get_chat_member(PUBLIC_CHANNEL_ID, user.id)
        
        valid_status = ["member", "administrator", "creator"]

        if private_member.status in valid_status and public_member.status in valid_status:
            # ভেরিফিকেশন সফল!
            await query.answer("✅ Verification Successful!", show_alert=True)
            # ইউজারকে ভেরিফাইড হিসেবে মার্ক করি
            set_user_verified(user.id, True)
            # পুরনো মেসেজ ডিলিট করে নতুন মেনু দেখাই
            await query.message.delete()
            # query.message.chat_id ব্যবহার না করে query.effective_chat.id ব্যবহার করা ভালো
            await show_main_menu(query, context)
            
        else:
            await query.answer("❌ Please join both CSB channels first!", show_alert=True)
    
    except telegram.error.BadRequest as e:
        if "user not found" in str(e):
            await query.answer("❌ You must join both CSB channels first!", show_alert=True)
        else:
            await query.answer(f"⚠️ Error: {e}", show_alert=True)
            logger.error(f"Verification error: {e}")
    except Exception as e:
        await query.answer("❌ You must join both CSB channels first!", show_alert=True)
        logger.error(f"General verification error: {e}")

# ===============================
# 🔘 Main Menu Button Handler (আপডেটেড)
# ===============================

async def main_menu_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # বাটন ক্লিক রিসিভড
    
    data = query.data
    context.user_data["next_step"] = None # আগের কোনো state থাকলে ক্লিয়ার করি

    if data == "gen_image":
        context.user_data["next_step"] = "image_prompt"
        await query.message.edit_text("✨ Send your prompt for **Image Generation** (e.g., *a white cat sleeping*)...\n\nOr click /cancel to go back.", parse_mode="Markdown")
    
    elif data == "gen_video":
        context.user_data["next_step"] = "video_prompt"
        await query.message.edit_text("✨ Send your prompt for **Video Generation** (e.g., *a robot walking in Dhaka city*)...\n\nOr click /cancel to go back.", parse_mode="Markdown")

    elif data == "my_profile":
        await show_profile(query, context)

    elif data == "back_to_menu":
        await show_main_menu(update, context)

    # contact_dev বাটনটি URL বাটনে পরিণত হওয়ায় এই হ্যান্ডলারের আর প্রয়োজন নেই

# ===============================
# 🎬 CSB AI TEXT → VIDEO (সংশোধিত)
# ===============================

async def generate_video(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str):
    user = update.message.from_user
    chat_id = update.message.chat_id
    user_data = get_user_data(user.id, user.first_name)
    
    # 1. ক্রেডিট চেক
    if user_data["credits"] < 1:
        # URL বাটন ব্যবহার করা হয়েছে
        keyboard = [[InlineKeyboardButton(f"Contact Developer (@{DEVELOPER_USERNAME})", url=f"https://t.me/{DEVELOPER_USERNAME}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_html("❌ **Out of Credits!**\n\nYou don't have enough credits to generate a video. Please contact the developer to recharge.", reply_markup=reply_markup, disable_web_page_preview=True)
        return

    generating = await update.message.reply_html("⏳ CSB AI is generating your video, please wait...")
    await context.bot.send_chat_action(chat_id=chat_id, action="upload_video")

    try:
        encoded_prompt = urllib.parse.quote(prompt)
        api_url = f"https://api.yabes-desu.workers.dev/ai/tool/txt2video?prompt={encoded_prompt}"
        response = requests.get(api_url, timeout=60) # 60 সেকেন্ড টাইমআউট
        data = response.json()

        if data.get("success"):
            video_url = data["url"]
            # নতুন ক্যাপশন (ফুটার সহ)
            caption = f"""
🎥 CSB AI Video Generated! (1 🪙 Credit Used)

👤 User: {user.first_name}
✨ Prompt: {prompt}
🎯 Status: Success ✅

━━━━━━━━━━━━━━━
<b>🔧 Powered by:</b> <a href="{POWERED_BY_LINK}">Cyber Sentinel Bangladesh</a>
<b>👨‍💻 Developer:</b> <a href="https://t.me/{DEVELOPER_USERNAME}">BIJOY (CSB)</a>
"""
            # 🟢 FIX: নিচের লাইন থেকে 'disable_web_page_preview=True' সরানো হয়েছে
            await context.bot.send_video(
                chat_id=chat_id, 
                video=video_url, 
                caption=caption, 
                parse_mode="HTML"
            )
            
            await context.bot.delete_message(chat_id=chat_id, message_id=generating.message_id)
            
            # 2. ক্রেডিট ও স্ট্যাটাস আপডেট
            update_user_credits(user.id, -1) # 1 ক্রেডিট কাটা হলো
            increment_user_stat(user.id, "video")
            
        else:
            await generating.edit_text("❌ CSB Video Generation Failed! (API Error)", parse_mode="HTML")
    
    except requests.exceptions.Timeout:
        await generating.edit_text("⚠️ Error: The request timed out. Please try again later.", parse_mode="HTML")
    except Exception as e:
        await generating.edit_text(f"⚠️ Error: {e}", parse_mode="HTML")
        logger.error(f"Video Gen Error: {e}")

# ===============================
# 🖼️ CSB AI TEXT → IMAGE (আপডেটেড)
# ===============================

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str):
    user = update.message.from_user
    chat_id = update.message.chat_id
    user_data = get_user_data(user.id, user.first_name)

    # 1. ক্রেডিট চেক
    if user_data["credits"] < 1:
        # URL বাটন ব্যবহার করা হয়েছে
        keyboard = [[InlineKeyboardButton(f"Contact Developer (@{DEVELOPER_USERNAME})", url=f"https://t.me/{DEVELOPER_USERNAME}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_html("❌ **Out of Credits!**\n\nYou don't have enough credits to generate an image. Please contact the developer to recharge.", reply_markup=reply_markup, disable_web_page_preview=True)
        return

    generating = await update.message.reply_html("⏳ CSB AI is creating your image, please wait...")
    await context.bot.send_chat_action(chat_id=chat_id, action="upload_photo")

    try:
        encoded_prompt = urllib.parse.quote(prompt)
        api_url = f"https://text2img.hideme.eu.org/image?prompt={encoded_prompt}&model=flux"
        response = requests.get(api_url, timeout=60)
        response.raise_for_status()

        if response.status_code == 200:
            # নতুন ক্যাপশন (ফুটার সহ)
            caption = f"""
🖼️ CSB AI Image Generated! (1 🪙 Credit Used)

👤 User: {user.first_name}
✨ Prompt: {prompt}
🎯 Status: Success ✅

━━━━━━━━━━━━━━━
<b>🔧 Powered by:</b> <a href="{POWERED_BY_LINK}">Cyber Sentinel Bangladesh</a>
<b>👨‍💻 Developer:</b> <a href="https://t.me/{DEVELOPER_USERNAME}">BIJOY (CSB)</a>
"""
            await context.bot.send_photo(
                chat_id=chat_id, photo=response.content, caption=caption, parse_mode="HTML"
            )
            await context.bot.delete_message(chat_id=chat_id, message_id=generating.message_id)

            # 2. ক্রেডিট ও স্ট্যাটাস আপডেট
            update_user_credits(user.id, -1) # 1 ক্রেডিট কাটা হলো
            increment_user_stat(user.id, "image")

        else:
            await generating.edit_text("❌ CSB Image Generation Failed! (API Error)", parse_mode="HTML")
    
    except requests.exceptions.Timeout:
        await generating.edit_text("⚠️ Error: The request timed out. Please try again later.", parse_mode="HTML")
    except Exception as e:
        await generating.edit_text(f"⚠️ Error: {e}", parse_mode="HTML")
        logger.error(f"Image Gen Error: {e}")

# ===============================
# 🧠 ADMIN PANEL (আপনার প্রথম কোড অনুযায়ী)
# ===============================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 You are not authorized to access CSB Admin Panel.")
        return

    keyboard = [
        [InlineKeyboardButton("📊 Total Users", callback_data="admin_total_users")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
        [InlineKeyboardButton("💸 Set User Credits", callback_data="admin_set_credits")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_html("⚙️ **CSB Admin Panel**\nChoose an option below:", reply_markup=reply_markup)

# ===============================
# 🔘 ADMIN CALLBACKS (আপনার প্রথম কোড অনুযায়ী)
# ===============================

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    # অ্যাডমিন ভেরিফিকেশন
    if user_id not in ADMIN_IDS:
        await query.answer("🚫 Not authorized!", show_alert=True)
        return

    await query.answer()
    data = query.data

    if data == "admin_total_users":
        users = load_users()
        await query.message.edit_text(f"📊 Total CSB Users in Database: **{len(users)}**", parse_mode="Markdown")

    elif data == "admin_broadcast":
        await query.message.edit_text("📢 Send the message you want to broadcast to all users.\n\nOr click /cancel to go back.")
        context.user_data["next_step"] = "admin_broadcast_message" # পরবর্তী ইনপুটের জন্য স্টেট সেট

    elif data == "admin_set_credits":
        await query.message.edit_text("💸 Send the **User ID** of the user you want to set credits for.\n\nOr click /cancel to go back.")
        context.user_data["next_step"] = "admin_set_credits_userid" # স্টেট সেট

# ===============================
# 💬 Message Handler (সকল ইনপুট)
# ===============================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # মেসেজটি এডিট করা হলে ইগনোর করুন
    if not update.message:
        return
        
    user_id = update.message.from_user.id
    text = update.message.text
    
    # কোনো কারণে text না থাকলে (e.g. sticker) ইগনোর করুন
    if not text:
        return
        
    next_step = context.user_data.get("next_step")

    # --- অ্যাডমিন ইনপুট হ্যান্ডলিং ---
    if user_id in ADMIN_IDS:
        if next_step == "admin_broadcast_message":
            context.user_data["next_step"] = None # স্টেট ক্লিয়ার
            users = load_users()
            success = 0
            failed = 0
            msg = await update.message.reply_text(f"📢 Broadcasting... Please wait. (0/{len(users)})")
            
            for i, uid in enumerate(users.keys()):
                try:
                    await context.bot.send_message(chat_id=uid, text=text, parse_mode="HTML", disable_web_page_preview=True)
                    success += 1
                except Exception as e:
                    logger.warning(f"Broadcast failed for {uid}: {e}")
                    failed += 1
                
                # প্রতি 20 জনে স্ট্যাটাস আপডেট
                if (i + 1) % 20 == 0:
                    try:
                        await msg.edit_text(f"📢 Broadcasting... Please wait. ({success}/{len(users)})")
                    except:
                        pass # এডিট করতে ফেইল করলে সমস্যা নেই

            await msg.edit_text(f"✅ Broadcast sent to {success} users.\nFailed for {failed} users.")
            return # অ্যাডমিন কাজ শেষ

        elif next_step == "admin_set_credits_userid":
            if not text.isdigit():
                await update.message.reply_text("❌ Invalid User ID. Please send a valid numeric User ID.")
                return # স্টেট ক্লিয়ার না করে আবার ইনপুটের অপেক্ষা
            
            context.user_data["target_user_id"] = text # টার্গেট ইউজার আইডি সেভ
            context.user_data["next_step"] = "admin_set_credits_amount" # পরবর্তী স্টেটে যাই
            await update.message.reply_text(f"OK. Now send the **total amount** of credits for User ID: `{text}` (e.g., `1000`)", parse_mode="Markdown")
            return

        elif next_step == "admin_set_credits_amount":
            if not text.isdigit():
                await update.message.reply_text("❌ Invalid amount. Please send a numeric value (e.g., `1000`).")
                return

            target_user_id = context.user_data.get("target_user_id")
            amount = int(text)
            
            try:
                set_user_credits(target_user_id, amount)
                await update.message.reply_text(f"✅ Success! User `{target_user_id}` now has **{amount}** credits.", parse_mode="Markdown")
                
                # টার্গেট ইউজারকে নোটিফিকেশন পাঠানো (আপনার অনুরোধ অনুযায়ী)
                try:
                    await context.bot.send_message(chat_id=target_user_id, text=f"🎉 Admin has set your credits! You now have **{amount}** 🪙 credits.", parse_mode="Markdown")
                except Exception as e:
                    await update.message.reply_text(f"⚠️ Note: Admin was notified, but couldn't notify user {target_user_id}. Error: {e}")

            except Exception as e:
                await update.message.reply_text(f"⚠️ Failed to set credits: {e}")
                
            context.user_data.pop("target_user_id", None)
            context.user_data["next_step"] = None # কাজ শেষ, স্টেট ক্লিয়ার
            return

    # --- ইউজার প্রম্পট হ্যান্ডলিং ---
    
    # ইউজার ভেরিফাইড কিনা চেক করি (খুবই জরুরি)
    user_data = get_user_data(user_id, update.message.from_user.first_name)
    if not user_data.get("is_verified", False):
        await update.message.reply_text("Please /start the bot and verify by joining our channels first.")
        return

    if next_step == "image_prompt":
        context.user_data["next_step"] = None # স্টেট ক্লিয়ার
        await generate_image(update, context, text) # জেনারেটর ফাংশনে প্রম্পট পাস
        await show_main_menu(update, context) # কাজ শেষে আবার মেনু দেখাই

    elif next_step == "video_prompt":
        context.user_data["next_step"] = None # স্টেট ক্লিয়ার
        await generate_video(update, context, text) # জেনারেটর ফাংশনে প্রম্পট পাস
        await show_main_menu(update, context) # কাজ শেষে আবার মেনু দেখাই
    
    # যদি কোনো স্টেট সেট করা না থাকে, কিন্তু ইউজার মেসেজ দেয়
    elif not next_step:
        # ইউজার ভেরিফাইড হলে তাকে মেইন মেনু দেখাই
        await show_main_menu(update, context)


# ===============================
# ↩️ Cancel Command (নতুন)
# ===============================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """যেকোনো স্টেট (prompt বা admin) ক্যানসেল করে মেইন মেনুতে ফিরে যায়"""
    user_id = update.message.from_user.id
    context.user_data.pop("next_step", None)
    context.user_data.pop("target_user_id", None)
    
    await update.message.reply_text("Action cancelled. Returning to main menu.")
    
    # ইউজার ভেরিফাইড হলেই শুধু মেইন মেনু দেখাবে
    user_data = get_user_data(user_id, update.message.from_user.first_name)
    if user_data.get("is_verified", False):
        await show_main_menu(update, context)

# ===============================
# 🚀 MAIN FUNCTION
# ===============================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ইউজার কমান্ডস
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("cancel", cancel)) # ক্যানসেল হ্যান্ডলার

    # বাটন হ্যান্ডলার (CallbackQueryHandlers)
    app.add_handler(CallbackQueryHandler(verify_callback, pattern="^verify$"))
    app.add_handler(CallbackQueryHandler(admin_buttons, pattern="^admin_"))
    # অন্যান্য সকল বাটন (gen_image, my_profile, etc.)
    # main_menu_button_handler কে সবার শেষে রাখা ভালো যাতে নির্দিষ্ট প্যাটার্নগুলো আগে ম্যাচ হয়
    app.add_handler(CallbackQueryHandler(main_menu_button_handler)) 

    # মেসেজ হ্যান্ডলার (সবচেয়ে গুরুত্বপূর্ণ)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ CSB AI BOT is now running under Cyber Sentinel Bangladesh...")
    app.run_polling()

# ===============================
# 🔰 RUN BOT
# ===============================

if __name__ == "__main__":

    main()

