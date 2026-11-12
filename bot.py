import os
import asyncio
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

# Load local .env if available
load_dotenv()

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = int(os.getenv("PORT", "8070"))

# Simple HTTP Health Check Handler for Kubernetix
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - 24/7 Bot is healthy")

    def log_message(self, format, *args):
        # Silence access logs to keep log output clean
        return

def start_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthCheckHandler)
    logger.info(f"Health check HTTP server listening on port {PORT}")
    server.serve_forever()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "there"
    welcome_text = (
        f"Hello {user_name}! 👋\n\n"
        "I am your AI Chatbot running 24/7 on Kubernetix!\n\n"
        "Commands:\n"
        "/start - Welcome message\n"
        "/help - Available commands\n"
        "/ping - Check bot health & status\n\n"
        "Send me any text message and I will reply!"
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 **Bot Help**\n\n"
        "/start - Start & welcome\n"
        "/help - Show this guide\n"
        "/ping - Check if bot is responsive\n"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong! Bot is active 24/7 on Kubernetix.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    response = f"Echo: {user_text}"
    await update.message.reply_text(response)

def main():
    if not TOKEN:
        raise ValueError("Error: TELEGRAM_BOT_TOKEN environment variable not set!")

    # Start health check server on port 8070 in background thread
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    logger.info("Initializing Telegram bot application...")
    app = ApplicationBuilder().token(TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot starting polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
