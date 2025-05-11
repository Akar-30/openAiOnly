import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from processing import process_text, process_voice

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
BOT_USERNAME = "@KurdiAiBot"  # Replace with your bot's username

# Ensure voice_messages directory exists
VOICE_DIR = "voice_messages"
os.makedirs(VOICE_DIR, exist_ok=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Send me text or a voice message and I'll process it!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
    This bot can process both text and voice messages.
    
    Just send me:
    - Any text message
    - A voice note
    
    I'll process it and send you back the result.
    """
    await update.message.reply_text(help_text)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    response = process_text(text)
    await update.message.reply_text(response)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        voice = update.message.voice
        voice_file = await voice.get_file()
        
        # Create unique file path
        file_path = os.path.join(VOICE_DIR, f"{voice.file_id}.ogg")
        
        # Download the voice file (corrected method name)
        await voice_file.download_to_drive(file_path)
        
        # Process the voice message
        response = process_voice(file_path)
        
        await update.message.reply_text(response)
        
        # Optional: Remove the file after processing
        os.remove(file_path)
        
    except Exception as e:
        print(f"Error processing voice message: {e}")
        await update.message.reply_text("Sorry, I couldn't process that voice message. Please try again.")

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")
    await update.message.reply_text("An error occurred. Please try again.")

if __name__ == "__main__":
    print("Starting bot...")
    app = Application.builder().token(TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))

    # Message handlers
    app.add_handler(MessageHandler(filters.TEXT, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Error handler
    app.add_error_handler(error)

    print("Polling...")
    app.run_polling(poll_interval=3)