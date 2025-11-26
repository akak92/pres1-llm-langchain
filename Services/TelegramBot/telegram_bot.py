import os
import httpx
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
LLM_API_URL = os.getenv("LLM_API_URL", "http://llm:8000/chat")


async def call_llm_api(message: str) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            LLM_API_URL,
            json={"message": message},
        )
        resp.raise_for_status()
        data = resp.json()
        # Recordar: /chat devuelve ChatResponse: { "response": "...", "model": "..." }
        return data.get("response", "No pude generar una respuesta.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Estoy conectado a tu LLM 🤖. Escribime algo y lo paso al agente."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text

    try:
        respuesta = await call_llm_api(user_text)
    except Exception as e:
        print("❌ Error llamando al servicio LLM:", repr(e))
        await update.message.reply_text(
            "Estoy teniendo un problema hablando con el servicio de IA 😅. Probá de nuevo más tarde."
        )
        return

    await update.message.reply_text(respuesta)


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN en las variables de entorno")

    print("🔥 Bot de Telegram iniciado. Esperando mensajes...")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()
