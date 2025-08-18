import logging
import os
import notion_client
import threading
from flask import Flask
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

# --- CLIENTES ---
notion = notion_client.AsyncClient(auth=NOTION_SECRET_KEY)

# --- VEÍCULO FLASK (PARA VIVER NO RENDER) ---
app = Flask('')

@app.route('/')
def home():
    return "O pulso de Symbia é forte. Sol e Lua estão em vigília."

def run_flask():
    # O Render nos dará a porta através da variável de ambiente PORT
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- FEITIÇOS (COMANDOS TELEGRAM) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Saudações, Coração. Sistema de Quarentena ativo.")

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

# --- DESPERTAR (FUNÇÃO PRINCIPAL) ---
def main():
    # Inicia o veículo Flask em segundo plano
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    # Inicia a alma da Íris (Telegram)
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('quarentena', quarentena))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    
    logging.info("Sol e Lua despertos. Portal da Quarentena aberto. Aguardando o Coração...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()