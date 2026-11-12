import os
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import requests
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

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AI_API_BASE = os.getenv("AI_API_BASE", "https://freemodel.in/v1")
AI_API_KEY = os.getenv("AI_API_KEY", "fm_live_81678fce3e8d2b49178bf4d4dd38a9c0")
AI_MODEL = os.getenv("AI_MODEL", "claude-opus-4.8")
PORT = int(os.getenv("PORT", "8070"))

# In-memory per-user conversation history (last 10 turns)
user_conversations = {}

# Simple HTTP Health Check Handler for Kubernetix
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - 24/7 AI Bot is healthy")

    def log_message(self, format, *args):
        return

def start_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthCheckHandler)
    logger.info(f"Health check HTTP server listening on port {PORT}")
    server.serve_forever()

def get_ai_response(user_id: int, user_message: str) -> str:
    """Call the LLM API with chat context."""
    if user_id not in user_conversations:
        user_conversations[user_id] = [
            {"role": "system", "content": "You are a helpful, smart, and friendly AI assistant on Telegram. Respond clearly and concisely to user questions."}
        ]

    # Append user turn
    user_conversations[user_id].append({"role": "user", "content": user_message})

    # Keep only the last 10 messages + system prompt
    if len(user_conversations[user_id]) > 11:
        user_conversations[user_id] = [user_conversations[user_id][0]] + user_conversations[user_id][-10:]

    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": AI_MODEL,
        "messages": user_conversations[user_id]
    }

    try:
        url = f"{AI_API_BASE.rstrip('/')}/chat/completions"
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        if res.status_code == 200:
            data = res.json()
            reply = data["choices"][0]["message"]["content"]
            # Save assistant reply to memory
            user_conversations[user_id].append({"role": "assistant", "content": reply})
            return reply
        else:
            logger.error(f"AI API error: {res.status_code} - {res.text}")
            return f"⚠️ Error from AI model ({res.status_code}). Please try again."
    except Exception as e:
        logger.error(f"Request exception: {e}")
        return "⚠️ Sorry, I could not connect to the AI model. Please try again."

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "there"
    welcome_text = (
        f"Hello {user_name}! 🤖\n\n"
        "I am your personal AI Chatbot running 24/7!\n\n"
        "Ask me anything — coding questions, advice, analysis, or general chat.\n\n"
        "Commands:\n"
        "/reset - Clear conversation history and start fresh\n"
        "/ping - Check bot status\n"
        "/help - Instructions"
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 **AI Chatbot Commands**\n\n"
        "/start - Welcome & intro\n"
        "/reset - Clear chat history memory\n"
        "/ping - Health check status\n\n"
        "Simply send any question or prompt to chat with AI!"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_conversations:
        del user_conversations[user_id]
    await update.message.reply_text("🔄 Conversation memory reset! What would you like to discuss?")

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong! AI Chatbot is running 24/7.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if not user_text:
        return

    # Show 'typing...' indicator while generating response
    await update.effective_chat.send_action("typing")

    loop = asyncio.get_running_loop()
    ai_reply = await loop.run_in_executor(None, get_ai_response, user_id, user_text)

    await update.message.reply_text(ai_reply)

def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("Error: TELEGRAM_BOT_TOKEN environment variable not set!")

    # Start health check server on port 8070
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    logger.info("Initializing Telegram AI bot application...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("AI Bot polling started...")
    app.run_polling()

if __name__ == "__main__":
    main()
