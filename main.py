import os
import json
import logging
import aiohttp
import asyncio
from dotenv import load_dotenv
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import Command
from aiogram import Bot, Dispatcher, Router



# CONFIGURE LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # Logging
logger = logging.getLogger(__name__)

# LOAD ENVIRONMENT VARIABLES
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_CRITIC_API")
API_URL = os.getenv("API_ENDPOINT")
USER = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# INITIALIZE BOT
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router) # Register router



# SUPPORT FUNCTION
## Function to split long messages
MAX_LEN = 2048
async def splitting_long_message(chat_id: int, text):
    # Handle case when text is a dictionary
    if isinstance(text, dict):
        text = json.dumps(text, ensure_ascii=False, indent=2)
        
    if not text or (isinstance(text, str) and not text.strip()):
        await bot.send_message(chat_id, "Получен пустой ответ от API.")
        return

    if len(text) <= MAX_LEN:
        await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)
        logger.info(f"Сообщение отправлено пользователю {chat_id}")
        return
    
    parts = [text[i:i+MAX_LEN] for i in range(0, len(text), MAX_LEN)]
    for part in parts:
        try:
            await bot.send_message(chat_id, part, parse_mode=ParseMode.HTML)
        except Exception as e:
            await bot.send_message(chat_id, part)
            logging.error(f"Ошибка при отправке HTML: {e}")

    logger.info(f"Сообщения отправлена пользователю {chat_id}")



## Initialize user services data. JSON file to store user service preferences
USER_SERVICES_FILE = "user_services.json"
def load_user_services():
    if os.path.exists(USER_SERVICES_FILE):
        try:
            with open(USER_SERVICES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error decoding {USER_SERVICES_FILE}. Creating a new one.")
    return {}

### Save user services data
def save_user_services(user_services):
    with open(USER_SERVICES_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_services, f, ensure_ascii=False, indent=2)

### Global variable to store user service preferences
user_services = load_user_services()

### Get user service type or default if not found
def get_user_service(user_id):
    user_id_str = str(user_id)
    if user_id_str not in user_services:
        user_services[user_id_str] = "alfa_friday"
        save_user_services(user_services)
    return user_services[user_id_str]



# FUNCTION FOR SYSTEM MESSAGE
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Готов помогать. Выбери в «Меню» какой сервис тебе нужен. По умолчанию включен «Альфа-Пятница».")

@router.message(Command("alfa_friday"))
async def alfa_friday(message: Message):
    user_id = str(message.from_user.id)
    user_services[user_id] = "alfa_friday"
    save_user_services(user_services)
    await message.answer("Включен сервис «Альфа-Пятница».")

@router.message(Command("static_trainer"))
async def static_trainer(message: Message):
    user_id = str(message.from_user.id)
    user_services[user_id] = "static_trainer"
    save_user_services(user_services)
    await message.answer("Включен сервис «Статичный тренер».")

@router.message(Command("spoiler_trainer"))
async def spoiler_trainer(message: Message):
    user_id = str(message.from_user.id)
    user_services[user_id] = "spoiler_trainer"
    save_user_services(user_services)
    await message.answer("Включен сервис «Тренер-спойлер».")

@router.message(Command("stories_trainer"))
async def stories_trainer(message: Message):
    user_id = str(message.from_user.id)
    user_services[user_id] = "stories_trainer"
    save_user_services(user_services)
    await message.answer("Включен сервис «Тренер в видео».")

@router.message(Command("final_trainer"))
async def final_trainer(message: Message):
    user_id = str(message.from_user.id)
    user_services[user_id] = "final_trainer"
    save_user_services(user_services)
    await message.answer("Включен сервис «Финальный тренер».")

@router.message(Command("speach_trainer"))
async def speach_trainer(message: Message):
    user_id = str(message.from_user.id)
    user_services[user_id] = "speach_trainer"
    save_user_services(user_services)
    await message.answer("Включен сервис «Прямая речь».") 



# HANDLER FOR TEXT MESSAGES
@router.message()
async def handle_message(message: Message):
    # Check if the message is a text message
    if not message.text:
        return 
    
    user_query = message.text
    user_id = message.from_user.id
    
    # Log that we received a message
    logger.info(f"Получено сообщение от пользователя {user_id}")
    
    # Send a status message
    processing_message = await message.answer("Обрабатываю запрос...")
    
    # Get the user's selected service type
    service_type = get_user_service(user_id)
    
    # Prepare the request payload
    payload = {
        "query": user_query,
        "type": service_type
    }
    
    try:
        # Send the request to the API
        async with aiohttp.ClientSession() as session:
            headers = {"Content-Type": "application/json"}
            
            # Log that we're sending a request to API
            logger.info(f"Отправка запроса в API от пользователя {user_id}")
            
            async with session.post(API_URL, json=payload, auth=aiohttp.BasicAuth(USER, PASSWORD), headers=headers, timeout=60) as response:
                # Delete processing message
                await bot.delete_message(chat_id=message.chat.id, message_id=processing_message.message_id)
                
                if response.status == 200:

                    api_response = await response.json()
                    # print(json.dumps(api_response, ensure_ascii=False, indent=2))
                    # await splitting_long_message(message.chat.id, api_response)

                    if isinstance(api_response, dict):
                        response_content = api_response.get("response", {})
                        logger.info(f"Type of response_content: {type(response_content)}")
                        
                        if isinstance(response_content, dict) and "text" in response_content:
                            response_send = response_content["text"]
                        elif isinstance(response_content, dict) and "result" in response_content and "message" in response_content:
                            response_result = response_content["result"]
                            response_message = response_content["message"]
                            if response_message in ['OK', 'ОК']:
                                response_send = f"<b>Рецензия:</b>\n{response_message}"
                            else:
                                examples = f'<b>Возможный вариант исправления:</b>\n{response_result[0]}' if len(response_result) == 1 else f'<b>Возможные варианты исправлений:</b>\n• {"\n• ".join(response_result)}'
                                response_send = f"<b>Рецензия:</b>\n{response_message}\n\n{examples}"
                        else:
                            response_send = "Структура ответа API не соответствует ожидаемой"
                    else:
                        response_send = "Структура ответа API не соответствует ожидаемой"
                    await splitting_long_message(message.chat.id, response_send)
                    
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
    except asyncio.TimeoutError:
        await message.answer("Превышено время ожидания ответа от API.")
    except Exception as e:
        error_message = f"Произошла ошибка: {str(e)}"
        logging.error(error_message)
        await message.answer("Извините, произошла ошибка при обработке вашего запроса.")




# MAIN FUNCTION TO START THE BOT
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())