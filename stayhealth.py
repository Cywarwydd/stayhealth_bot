from aiocron import crontab
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
import asyncio
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from dotenv import load_dotenv
import os

### Ваня
# Указываем токен нашего бота
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Создаем бот и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Словарь для хранения данных пользователей
user_data = {}


# Добавили тестовые вопросы и категории
TESTS = {
    "Тревога": [
        "Я беспокоюсь о независящих от меня обстоятельств",
        "Бывает такое, что мне тяжело расслабиться",
        "Я сильно нервничаю перед важным событием"
    ],
    "Агрессия": [
        "Я повышаю голос, чтобы меня услышали",
        "Бывает я злюсь из-за того что глухая и не слышу шуток друзей ",
        "Мне хочется спорить, потому что другие не правы"
    ],
    "Стресс": [
        "Я чувствую усталость даже после отдыха",
        "В повседневной жизни мне приходится сталкиваться с напряжением",
        "Мне трудно справляться с базовыми задачами"
    ],
    "Апатия": [
        "В последнее время я чувствую себя подавленным",
        "Я замечаю, что потерял интерес к тому, что раньше приносило удовольствие",
        "Я ощущаю недостаток мотивации"
    ]
}
###

### Кристина
# Функция для получения текущей даты
def get_current_date():
    return datetime.now().date()

# Функция обнуления результатов
def reset_weekly_data(user_id):
    today = get_current_date()
    # Проверяем, если сегодня понедельник
    if today.weekday() == 0:  # 0 — это понедельник
        # Сбрасываем результаты прошлой недели
        user_data[user_id]["week_results"] = {category: 0 for category in TESTS.keys()}
        user_data[user_id]["daily_scores"] = {}


# Функция проверки, прошел ли пользователь 4 теста за день 
def check_user_tests_completed(user_id):
    today = get_current_date()
    completed_tests = user_data[user_id]["last_completed"]
    return all(
        completed_tests.get(test, None) == today
        for test in TESTS.keys()
    )
# Функция для отправки напоминаний
async def send_reminders():
    while True:
        now = datetime.now()
        # Проверяем, наступило ли 20:00
        if now.hour == 20 and now.minute == 00:
            for user_id, data in user_data.items():
                if not check_user_tests_completed(user_id):
                    await bot.send_message(
                        user_id,
                        "Привет ꒰ᐢ. .ᐢ꒱! Настало время для ежедневного опроса"
                    )
            await asyncio.sleep(60)  # Ждем 1 минуту, чтобы избежать повторного уведомления
        await asyncio.sleep(30)  # Проверяем каждые 30 секунд
###

### Ваня
# Команда /start
@dp.message_handler(commands=["start"])
async def start_game(message: types.Message):
    user_id = message.from_user.id
    
    # Инициализация данных пользователя
    if user_id not in user_data:
        user_data[user_id] = {
            "week_results": {category: 0 for category in TESTS.keys()},
            "daily_results": {category: 0 for category in TESTS.keys()},
            "last_completed": {},  # Для отслеживания даты прохождения тестов
            "current_test": None,
            "current_question_index": 0,
            "daily_scores": {}  # Данные по дням недели
        }
    
    # Приветствие в зависимости от времени суток
    greeting = get_greeting()
    await message.answer(
        f"{greeting} Это помощник для мониторинга психологического состояния здоровья \n\n"
        "Как он работает\n"
        "• короткие ежедневные тесты\n"
        "• всего 4 теста по 3 вопроса\n"
        "• в конце недели можно узнать результаты\n\n"
        "Внимание: проходить тесты можно только один раз в день\n\n"
        "Будьте здоровы ૮꒰⸝⸝>   <⸝⸝꒱ა\n\n"
        "Выберите тест, который хотите пройти ⁀➴",
        reply_markup=create_main_keyboard()
    )
    

# Функция для определения приветствия в зависимости от времени суток
def get_greeting():
    current_hour = datetime.now().hour
    if 6 <= current_hour < 12:
        return "Доброе утро!"
    elif 12 <= current_hour < 18:
        return "Добрый день!"
    elif 18 <= current_hour < 23:
        return "Добрый вечер!"
    else:
        return "Доброй ночи!"


# Создаем клавиатуры с тестами и кнопками для статистики
def create_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for test in TESTS.keys():
        keyboard.add(KeyboardButton(test))
    keyboard.add(KeyboardButton("Результаты дня"))
    keyboard.add(KeyboardButton("Результаты недели"))
    return keyboard
###

### Кристина
# Обработка выбора теста
@dp.message_handler(lambda message: message.text in TESTS.keys())
async def start_test(message: types.Message):
    user_id = message.from_user.id
    current_test = message.text

    # Сбрасываем данные, если сегодня понедельник
    reset_weekly_data(user_id)

    today = get_current_date()

    # Проверка, проходил ли пользователь этот тест сегодня
    if current_test in user_data[user_id]["last_completed"] and user_data[user_id]["last_completed"][current_test] == today:
        await message.answer(
            f"Вы уже проходили тест на {current_test} сегодня. Попробуйте снова завтра.",
            reply_markup=create_main_keyboard()
        )
        return

    user_data[user_id]["current_test"] = current_test
    user_data[user_id]["current_question_index"] = 0

    await send_question(user_id)


# Отправка вопросов
async def send_question(user_id):
    current_test = user_data[user_id]["current_test"]
    question_index = user_data[user_id]["current_question_index"]

    if question_index < len(TESTS[current_test]):
        question = TESTS[current_test][question_index]

        # Кнопки для ответа
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.add(
            KeyboardButton("Никогда"), 
            KeyboardButton("Редко"), 
            KeyboardButton("Иногда"), 
            KeyboardButton("Часто"), 
            KeyboardButton("Всегда")
        )

        await bot.send_message(user_id, question, reply_markup=keyboard)
    else:
        await finish_test(user_id)

# Добавили обработку ответов на вопросы
@dp.message_handler(lambda message: message.text in ["Никогда", "Редко", "Иногда", "Часто", "Всегда"])
async def handle_answer(message: types.Message):
    user_id = message.from_user.id
    answer_text = message.text

    # Оценка ответа
    score = {
        "Никогда": 0,
        "Редко": 1,
        "Иногда": 2,
        "Часто": 3,
        "Всегда": 4
    }[answer_text]

    current_test = user_data[user_id]["current_test"]
    user_data[user_id]["week_results"][current_test] += score
    user_data[user_id]["daily_results"][current_test] += score
    user_data[user_id]["current_question_index"] += 1

    # Сохраняем результат за сегодняшний день
    today = get_current_date()
    if today not in user_data[user_id]["daily_scores"]:
        user_data[user_id]["daily_scores"][today] = {category: 0 for category in TESTS.keys()}
    
    user_data[user_id]["daily_scores"][today][current_test] += score

    await send_question(user_id)

# Завершение теста
async def finish_test(user_id):
    current_test = user_data[user_id]["current_test"]
    today = get_current_date()

    # Обновление даты последнего прохождения
    user_data[user_id]["last_completed"][current_test] = today

    await bot.send_message(
        user_id,
        f"Вы завершили тест на {current_test}. Ваш результат сохранен.",
        reply_markup=create_main_keyboard()
    )
    user_data[user_id]["current_test"] = None
    user_data[user_id]["current_question_index"] = 0

# Функция для отображения метрики результатов с цветами
def create_progress_bar(score):
    if score <= 4:
        color = "🟩"  
    elif score <= 8:
        color = "🟨"  
    else:
        color = "🟥"  

    filled = color * score  # Заполненные блоки
    empty = "⬛" * (12 - score)  # Пустые блоки
    return filled + empty
###

### Ника
# Команда для результатов дня
@dp.message_handler(lambda message: message.text == "Результаты дня")
async def send_daily_results(message: types.Message):
    user_id = message.from_user.id
    results = user_data[user_id]["daily_results"]
    stats_message = ""

    for category, score in results.items():
        progress_bar = create_progress_bar(score)
        stats_message += f"{category}: {score}/12\n{progress_bar}\n\n"

    await message.answer(
        f"Ваши результаты за сегодня:\n\n{stats_message}",
        reply_markup=create_main_keyboard()
    )


# Команда для результатов недели
@dp.message_handler(lambda message: message.text == "Результаты недели")
async def send_week_results(message: types.Message):
    user_id = message.from_user.id
    stats_message = "Результаты по дням недели:\n\n"

    # Получаем начало недели (понедельник)
    today = get_current_date()
    start_of_week = today - timedelta(days=today.weekday())  # Понедельник

    total_score = 0
    for i in range(7):  # Проходим по всем дням недели
        day = start_of_week + timedelta(days=i)
        day_results = user_data[user_id]["daily_scores"].get(day, {category: 0 for category in TESTS.keys()})
        
        # Суммируем баллы за каждый день
        day_score = sum(day_results.values())
        total_score += day_score

        stats_message += f"\n{day.strftime('%A, %d %B')}: {day_score}/48\n"  

    # Добавляем суммарный результат за неделю
    stats_message += f"\n\nОбщий результат за неделю: {total_score}/336"  

    await message.answer(stats_message, reply_markup=create_main_keyboard())


async def send_weekly_summary():
    today = get_current_date()
    start_of_week = today - timedelta(days=today.weekday())  # Понедельник

    for user_id, data in user_data.items():
        total_score = 0
        active_days = 0
        all_tests_completed = False

        # Считаем общий балл за неделю и проверяем, пройдены ли все тесты
        for i in range(7):
            day = start_of_week + timedelta(days=i)
            day_results = data["daily_scores"].get(day, {category: -1 for category in TESTS.keys()})
            day_score = sum(day_results.values())

            if day_score >= 0:  # Учитываем только активные дни. Проверяем, были ли пройдены все тесты за день
                total_score += day_score
                active_days += 1
                all_tests_completed = True
            else:
                all_tests_completed = False
            
            

        # Если пользователь не участвовал всю неделю
        if active_days == 0:
            summary_message = (
                "На этой неделе вы не проходили тесты. Для получения рекомендаций важно регулярно участвовать. "
                "Начните следующую неделю с выполнения тестов — это поможет лучше понять ваше состояние."
            )
            await bot.send_message(user_id, summary_message)
            continue
        # Отправляем итоговое сообщение
        average_score = total_score / active_days
        if average_score > 24:  # Больше половины баллов в среднем за день
            summary_message = (
                f"Неделя завершена! Вы участвовали {active_days} из 7 дней. Ваш общий результат: {total_score}/{48 * active_days}.\n\n"
                "Ваши результаты выше среднего. Рекомендуем продолжать наблюдать за вашим состоянием и при необходимости обратиться к психологу."
            )
        elif average_score < 16:  # Меньше 1/3 баллов в среднем за день
            summary_message = (
                f"Неделя завершена! Вы участвовали {active_days} из 7 дней. Ваш общий результат: {total_score}/{48 * active_days}.\n\n"
                "Отлично! Ваши результаты показывают, что вы справляетесь. Продолжайте в том же духе!"
            )
        else:  # Средний результат
            summary_message = (
                f"Неделя завершена! Вы участвовали {active_days} из 7 дней. Ваш общий результат: {total_score}/{48 * active_days}.\n\n"
                "Ваши результаты находятся в среднем диапазоне. Продолжайте наблюдать за своим состоянием и заботьтесь о себе."
            )

        await bot.send_message(user_id, summary_message)

        # Поздравление за выполнение всех тестов
        if all_tests_completed:
            congrats_message = (
                "Поздравляем! 🎉 Вы прошли все тесты за эту неделю!\n\n"
                "Это замечательный показатель вашей ответственности и стремления работать над собой. "
                "Продолжайте в том же духе!"
            )
            medal_message = (
                "🏅"
            )
            await bot.send_message(user_id, congrats_message)
            await bot.send_message(user_id, medal_message)


# Тест эмуляция конца недели
@dp.message_handler(commands=["test_summary"])
async def test_summary_command(message: types.Message):
    await send_weekly_summary()


# Тест эмуляция конца недели медалька
@dp.message_handler(commands=["test_win_summary"])
async def test__win_summary_command(message: types.Message):
    user_id = message.from_user.id

    # Получаем начало недели (понедельник)
    today = get_current_date()
    start_of_week = today - timedelta(days=today.weekday())  # Понедельник

    # Эмулируем данные пользователя для полной недели с максимальными баллами
    user_data[user_id] = {
        "daily_scores": {}
    }
    for i in range(7):  # Заполняем данные для всех дней недели
        day = start_of_week + timedelta(days=i)
        user_data[user_id]["daily_scores"][day] = {category: 10 for category in TESTS.keys()}  # Максимальные баллы

    # Вызываем функцию подведения итогов
    await send_weekly_summary()

# Запускаем задачу в воскресенье в 23:59
@crontab("59 23 * * 0")
async def weekly_summary_cron():
    await send_weekly_summary()


# Обработка всех сообщений, которые не соответствуют никаким командам или тестам
@dp.message_handler()
async def handle_unknown_command(message: types.Message):
    await message.answer(
        "(◞‸ ◟) нет такой команды\n\n"
        "Пожалуйста, используйте кнопки или напишите /start, чтобы начать.",
        reply_markup=create_main_keyboard()
    )
###

### Ваня, Кристина
# Запуск бота
if __name__ == "__main__":
    # Запускаем фоновую задачу с напоминаниями
    loop = asyncio.get_event_loop()
    loop.create_task(send_reminders())
    
    executor.start_polling(dp, skip_updates=True)

