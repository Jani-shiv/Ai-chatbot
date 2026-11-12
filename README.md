# AI Chatbot for Telegram

A 24/7 Telegram bot ready for deployment on [Koyeb](https://koyeb.com) using Docker.

## Setup & Deployment to Koyeb

1. Go to [Koyeb Dashboard](https://app.koyeb.com/).
2. Click **Create App** / **Create Service**.
3. Select **GitHub** as the deployment method.
4. Select `Jani-shiv/Ai-chatbot` repository (branch `main`).
5. Choose **Dockerfile** as the build method.
6. Set **Service type** to **Worker** (or Web Service).
7. Under **Environment variables**, add:
   - `TELEGRAM_BOT_TOKEN` = `your_telegram_bot_token`
8. Click **Deploy**.
