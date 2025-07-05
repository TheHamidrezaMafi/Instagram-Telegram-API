
import json
import logging
from decouple import config
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters,ApplicationBuilder

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Define a `/start` command handler.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with an inline button that opens the web app."""
    keyboard = [
        [InlineKeyboardButton(
            text="Open MegaChat WebApp",
            web_app=WebAppInfo(url="https://megachat.ahmafi.ir/webapp/")
        )]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Here you can start the WebApp.",
        reply_markup=reply_markup
    )


# Handle incoming WebAppData
async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Print the received data and remove the button."""
    # Here we use `json.loads`, since the WebApp sends the data JSON serialized string
    # (see webappbot.html)
    data = json.loads(update.effective_message.web_app_data.data)
    # print(str(data))
    # await update.message.reply_html(
    #     text=(
    #         str(data)
    #     ),
    #     reply_markup=ReplyKeyboardRemove(),
    # )


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    token = config("TELEGRAM_TOKEN")
    application = ApplicationBuilder().token(token=token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()