import requests
import csv
from datetime import datetime
from urllib.parse import quote_plus
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# ---------------------------------
# ⚙️ CONFIGURATION
# ---------------------------------
BOT_TOKEN = "8215313956:AAGjohGolBP0qHrAQma3M1Q0a7tcegMMUR4"   # <-- Replace with your bot token
API_URL = "http://ifsc.razorpay.com/"
LOG_FILE = "ifsc_osint_log.csv"

# ---------------------------------
# 🧩 Helper: Format the Result Message
# ---------------------------------
def format_ifsc_data(data: dict, user: object, ifsc: str) -> str:
    imps = "✅" if data.get("IMPS") else "❌"
    neft = "✅" if data.get("NEFT") else "❌"
    rtgs = "✅" if data.get("RTGS") else "❌"
    upi = "✅" if data.get("UPI") else "❌"

    username = f"@{user.username}" if user.username else "N/A"

    text = (
        f"🕵️‍♂️ <b>IFSC OSINT Report</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>User:</b> {username}\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"⏰ <b>Timestamp:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"🏦 <b>Bank:</b> {data.get('BANK', 'N/A')}\n"
        f"🏛️ <b>Branch:</b> {data.get('BRANCH', 'N/A')}\n"
        f"📍 <b>Address:</b> {data.get('ADDRESS', 'N/A')}\n"
        f"🏙️ <b>City:</b> {data.get('CITY', 'N/A')} ({data.get('DISTRICT', 'N/A')})\n"
        f"🌆 <b>State:</b> {data.get('STATE', 'N/A')}\n"
        f"📮 <b>MICR:</b> {data.get('MICR', 'N/A')}\n"
        f"💳 <b>IFSC:</b> <code>{data.get('IFSC', 'N/A')}</code>\n"
        f"🏷️ <b>Bank Code:</b> {data.get('BANKCODE', 'N/A')}\n"
        f"📞 <b>Contact:</b> {data.get('CONTACT', 'N/A')}\n"
        f"🌍 <b>ISO3166:</b> {data.get('ISO3166', 'N/A')}\n\n"
        f"💰 <b>Payment Systems:</b>\n"
        f" • IMPS: {imps}\n"
        f" • NEFT: {neft}\n"
        f" • RTGS: {rtgs}\n"
        f" • UPI: {upi}\n"
    )
    return text


# ---------------------------------
# 🗂️ Helper: Log to CSV
# ---------------------------------
def log_to_csv(user, ifsc, data):
    headers = [
        "timestamp", "user_id", "username", "ifsc", "bank", "branch",
        "city", "state", "district", "micr", "address", "neft",
        "rtgs", "imps", "upi", "source_url"
    ]

    try:
        with open(LOG_FILE, "x", newline='', encoding="utf-8") as f:
            csv.writer(f).writerow(headers)
    except FileExistsError:
        pass

    with open(LOG_FILE, "a", newline='', encoding="utf-8") as f:
        csv.writer(f).writerow([
            datetime.now().isoformat(),
            user.id,
            user.username,
            ifsc,
            data.get("BANK", ""),
            data.get("BRANCH", ""),
            data.get("CITY", ""),
            data.get("STATE", ""),
            data.get("DISTRICT", ""),
            data.get("MICR", ""),
            data.get("ADDRESS", ""),
            data.get("NEFT", ""),
            data.get("RTGS", ""),
            data.get("IMPS", ""),
            data.get("UPI", ""),
            f"{API_URL}{ifsc}"
        ])


# ---------------------------------
# 🚀 Start Command
# ---------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Welcome to the IFSC OSINT Intelligence Bot</b>\n\n"
        "Send me any IFSC code (e.g. <code>YESB0DNB002</code>) to fetch a full intelligence report.\n\n"
        "You’ll get:\n"
        "• Bank + Branch Details 🏦\n"
        "• Google Maps Location 🗺️\n"
        "• Payment Support 💰\n"
        "• API Source Link 🔗\n\n"
        "🧠 Use responsibly. All lookups are logged for OSINT tracking.",
        parse_mode="HTML"
    )


# ---------------------------------
# 📡 IFSC Lookup Handler
# ---------------------------------
async def ifsc_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ifsc = update.message.text.strip().upper()
    user = update.effective_user
    await update.message.reply_text(f"🔎 Searching for <b>{ifsc}</b> ...", parse_mode="HTML")

    try:
        res = requests.get(f"{API_URL}{ifsc}", timeout=10)
        if res.status_code == 200:
            data = res.json()

            msg = format_ifsc_data(data, user, ifsc)

            # Inline buttons
            maps_link = f"https://www.google.com/maps/search/{quote_plus(data.get('ADDRESS', ''))}"
            source_link = f"{API_URL}{ifsc}"

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🌍 Open Maps", url=maps_link),
                    InlineKeyboardButton("🔗 Source", url=source_link)
                ],
                [
                    InlineKeyboardButton("📤 Export Report", callback_data="export_report")
                ]
            ])

            await update.message.reply_text(msg, parse_mode="HTML", reply_markup=keyboard)
            log_to_csv(user, ifsc, data)

        else:
            await update.message.reply_text("❌ IFSC not found or invalid code.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")


# ---------------------------------
# 📤 Export Report Handler
# ---------------------------------
async def export_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        await query.message.reply_document(InputFile(LOG_FILE), caption="📁 IFSC OSINT Lookup Report")
    except Exception as e:
        await query.message.reply_text(f"⚠️ Could not export log: {e}")


# ---------------------------------
# 🧠 Main Function
# ---------------------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ifsc_lookup))
    app.add_handler(CallbackQueryHandler(export_report, pattern="export_report"))

    print("🛰️ IFSC OSINT Bot running with inline buttons...")
    app.run_polling()


# ---------------------------------
if __name__ == "__main__":
    main()
