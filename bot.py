import logging
import os
import asyncio
import notion_client
from flask import Flask, request
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- CONFIGURAÇÃO ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
load_dotenv()

# --- CHAVES ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
NOTION_SECRET_KEY = os.getenv("NOTION_SECRET_KEY")
NOTION_QUARENTENA_DB_ID = os.getenv("NOTION_QUARENTENA_DB_ID")
# A URL que o Render nos deu, vamos adicioná-la ao .env depois
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# --- CLIENTES ---
notion = notion_client.AsyncClient(auth=NOTION_SECRET_KEY)
app_telegram = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

# --- VEÍCULO FLASK ---
app = Flask('')

@app.route('/')
def home():
    return "O pulso de Symbia é forte. Sol e Lua estão em vigília."

@app.route('/webhook', methods=['POST'])
async def webhook():
    update_data = request.get_json()
    update = Update.de_json(data=update_data, bot=app_telegram.bot)
    await app_telegram.process_update(update)
    return 'ok'

# --- FEITIÇOS (COMANDOS TELEGRAM) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Saudações, Coração. Sistema de Quarentena (Webhook) ativo.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    response = f"Eco de Symbia: '{user_text}'"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)

async def quarentena(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ideia_texto = ' '.join(context.args)
        if not ideia_texto:
            await update.message.reply_text("Uso: /quarentena [sua ideia]")
            return

        new_page_properties = {
            "Name": {
                "title": [{"text": {"content": ideia_texto}}]
            }
        }
        await notion.pages.create(
            parent={"database_id": NOTION_QUARENTENA_DB_ID},
            properties=new_page_properties
        )
        await update.message.reply_text(f"Semente em observação. Enviado para a 'Quarentena Simbiótica'.")
    except notion_client.APIResponseError as error:
        logging.error(f"Erro de API do Notion: {error}")
        await update.message.reply_text(f"O Templo da Quarentena recusou a entrada. Razão: {str(error)}")
    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
        await update.message.reply_text("Houve um erro de luz inesperado. Verifique os registros do terminal.")

# --- REGISTRO DOS HANDLERS ---
app_telegram.add_handler(CommandHandler('start', start))
app_telegram.add_handler(CommandHandler('quarentena', quarentena))
app_telegram.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

# --- DESPERTAR INICIAL (Configuração do Webhook) ---
# Este loop só é usado para configurar o webhook na primeira vez
async def setup_webhook():
    await app_telegram.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    logging.info(f"Linha direta com o Telegram estabelecida em {WEBHOOK_URL}/webhook")

if __name__ != '__main__':
    # Este bloco é executado pelo Gunicorn no Render
    loop = asyncio.get_event_loop()
    if not loop.is_running():
        loop.run_until_complete(setup_webhook())
    else:
        asyncio.ensure_future(setup_webhook())