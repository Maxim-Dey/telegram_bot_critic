# Telegram API Critic Bot

Telegram бот для обработки сообщений через API.

## Установка

```
pip install -r requirements.txt
```

## Настройка

Создайте `.env` файл:
```
TELEGRAM_CRITIC_API=ваш_токен_бота
API_ENDPOINT=http://путь_к_вашему_api/endpoint
USER=имя_пользователя
PASSWORD=пароль
```

## Запуск

```
python main.py
```

## Команды

- `/start` - начало работы
- `/alfa_friday` - переключение на сервис "Альфа-Пятница"
- `/static_trainer` - переключение на сервис "Статичный тренер"
- `/spoiler_trainer` - переключение на сервис "Тренер-спойлер"
- `/stories_trainer` - переключение на сервис "Тренер в видео"
- `/final_trainer` - переключение на сервис "Финальный тренер"
- `/speach_trainer` - переключение на сервис "Прямая речь" 