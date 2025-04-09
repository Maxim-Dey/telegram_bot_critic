import os
import logging
import aiohttp
import asyncio
import json
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv


# CONFIGURE LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # Logging
logger = logging.getLogger(__name__)

# LOAD ENVIRONMENT VARIABLES
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_CRITIC_API")
API_URL = os.getenv("API_ENDPOINT")

# INITIALIZE BOT
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router) # Register router

# FUNCTION FOR SYSTEM MESSAGE
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Готов к труду и обороне.")

# SUPPORT FUNCTION
# Function to split long messages
MAX_LEN = 2048
async def send_long_message(chat_id: int, text: str):
    if not text or not text.strip():
        await bot.send_message(chat_id, "Получен пустой ответ от API.")
        return

    if len(text) <= MAX_LEN:
        await bot.send_message(chat_id, text, parse_mode="HTML")
        logger.info(f"Сообщение отправлено пользователю {chat_id}")
        return

    parts = [text[i:i+MAX_LEN] for i in range(0, len(text), MAX_LEN)]
    for part in parts:
        try:
            await bot.send_message(chat_id, part, parse_mode="HTML")
        except Exception as e:
            await bot.send_message(chat_id, part)
            logging.error(f"Ошибка при отправке HTML: {e}")
            
    logger.info(f"Сообщения отправлена пользователю {chat_id}")

# Handler for text messages
@router.message()
async def handle_message(message: Message):
    user_query = message.text
    user_id = message.from_user.id
    
    # Log that we received a message
    logger.info(f"Получено сообщение от пользователя {user_id}")
    
    # Send a status message
    processing_message = await message.answer("Обрабатываю ваш запрос...")
    
    # Prepare the request payload
    payload = {
        "query": user_query,
        "type": "alfa_friday"
    }
    
    try:
        # Send the request to the API
        async with aiohttp.ClientSession() as session:
            headers = {"Content-Type": "application/json"}
            
            # Log that we're sending a request to API
            logger.info(f"Отправка запроса в API от пользователя {user_id}")
            
            async with session.post(API_URL, json=payload, auth=aiohttp.BasicAuth('username', 'password'), headers=headers, timeout=60) as response:
                # Delete processing message
                await bot.delete_message(chat_id=message.chat.id, message_id=processing_message.message_id)
                
                if response.status == 200:
                    api_response = await response.json()
                    response_text = api_response.get("response", "Пустой ответ от API")
                    
                    # Log that we received a response from API
                    logger.info(f"Получен ответ от API для пользователя {user_id}")
                    
                    await send_long_message(message.chat.id, response_text)
                else:
                    error_text = f"Ошибка API: Код статуса {response.status}"
                    if response.headers.get("content-type", "").startswith("application/json"):
                        try:
                            error_details = await response.json()
                            error_text += f"\nДетали: {json.dumps(error_details, ensure_ascii=False)}"
                        except:
                            pass
                    await message.answer(error_text)
                    
    except aiohttp.ClientConnectorError:
        await message.answer("Не удалось подключиться к API. Проверьте URL и доступность сервера.")
    except aiohttp.ClientTimeout:
        await message.answer("Превышено время ожидания ответа от API.")
    except Exception as e:
        error_message = f"Произошла ошибка: {str(e)}"
        logging.error(error_message)
        await message.answer("Извините, произошла ошибка при обработке вашего запроса.")

# Main function to start the bot
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())