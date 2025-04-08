from dotenv import load_dotenv
import os
import asyncio
import aiohttp
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_CRITIC_API")
API_URL = "http://154.194.52.202/generate_text/generate"

# Maximum message length for Telegram
MAX_MESSAGE_LENGTH = 4096

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "Привет! Я готов отправлять ваши запросы на сервер и возвращать ответы. "
        "Просто напишите ваш запрос, и я обработаю его."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "Отправьте мне текстовое сообщение, и я передам его на обработку API."
    )

def split_message(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> list:
    """Split a message into chunks of maximum length."""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    while text:
        # If text is longer than max_length, find a good breaking point
        if len(text) > max_length:
            # Try to find the last space before max_length
            split_point = text[:max_length].rfind(' ')
            if split_point == -1:  # No space found, force split at max_length
                split_point = max_length
            
            chunks.append(text[:split_point])
            text = text[split_point:].lstrip()
        else:
            chunks.append(text)
            text = ""
    
    return chunks

async def send_api_request(query: str) -> str:
    """Send request to API and return the response."""
    payload = {
        "query": query,
        "type": "alfa_friday"
    }
    
    logger.info(f"Отправка запроса на API: {API_URL}")
    logger.info(f"Payload: {payload}")
    
    try:
        async with aiohttp.ClientSession() as session:
            logger.info("Соединение с API установлено")
            async with session.post(API_URL, json=payload) as response:
                logger.info(f"Получен ответ от API. Статус: {response.status}")
                response.raise_for_status()
                try:
                    result = await response.json()
                    logger.info("Успешно получен JSON-ответ")
                    return result
                except aiohttp.ContentTypeError:
                    # If response is not JSON, return text
                    text_response = await response.text()
                    logger.info(f"Получен текстовый ответ: {text_response[:100]}...")
                    return text_response
    except aiohttp.ClientError as e:
        error_msg = f"Ошибка при обращении к API: {str(e)}"
        logger.error(error_msg)
        return error_msg

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process user message, send to API, and respond."""
    user_message = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    
    logger.info(f"Получено сообщение от пользователя {username} (ID: {user_id}): {user_message[:50]}...")
    
    # Send "typing" action to indicate the bot is processing
    await update.message.chat.send_action(action="typing")
    
    # Send request to API
    logger.info("Отправка запроса на API...")
    api_response = await send_api_request(user_message)
    logger.info("Получен ответ от API")
    
    # Check if the response is an error message (string) or a JSON response
    if isinstance(api_response, str):
        response_text = api_response
        logger.info("Ответ в виде строки")
    else:
        # Extract the text from the JSON response (adjust based on actual API response structure)
        try:
            response_text = api_response.get('response', str(api_response))
            logger.info("Извлечен текст из JSON-ответа")
        except (AttributeError, TypeError):
            response_text = str(api_response)
            logger.info("Ошибка при извлечении текста из JSON, преобразовано в строку")
    
    # Split response if needed and send to user
    message_chunks = split_message(response_text)
    logger.info(f"Ответ разбит на {len(message_chunks)} частей")
    
    for i, chunk in enumerate(message_chunks):
        logger.info(f"Отправка части {i+1}/{len(message_chunks)} пользователю")
        await update.message.reply_text(chunk)
        logger.info(f"Часть {i+1} отправлена")

def main() -> None:
    """Start the bot."""
    # Create the Application
    logger.info("Запуск бота...")
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info(f"Бот запущен с токеном: {BOT_TOKEN[:5]}...")
    logger.info(f"API URL: {API_URL}")

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()