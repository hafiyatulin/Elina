import telebot
from telebot import types
import json
import os
from datetime import datetime

API_TOKEN = '7782481709:AAH6Nk_KnBSK3zOJtwoDQ4uOMjjfThJ5h20'
parent_id = 778248170  # Telegram ID родителя

bot = telebot.TeleBot(API_TOKEN)

# Инициализация файла
if os.path.exists("data.json"):
    with open("data.json", "r") as f:
        data = json.load(f)
else:
    data = {
        "balance": 0,
        "tasks": {
            "чтение": 3,
            "прогулка на улице": 4,
            "уборка на столе": 3,
            "уборка в комнате": 5,
            "чистка зубов": 2,
            "спорт": 4,
            "рисование": 3,
            "английский язык": 4,
            "душ": 3,
            "убрать лоток": 3,
            "покормить котов": 2,
            "помощь маме": 5,
            "застелить постель": 2
        },
        "rewards": {
            "15минут на телефоне": 15
        },
        "stats": {},
        "log": {},
        "actions": [],
        "last_reset": datetime.now().strftime("%Y-%m-%d")
    }

def save_data():
    with open("data.json", "w") as f:
        json.dump(data, f)
daily_goals = {
    "чистка зубов": {"target": 2, "count": 0},
    "застелить постель": {"target": 1, "count": 0},
    "чтение": {"target": 30, "minutes": 0},
    "прогулка на улице": {"target": 30, "minutes": 0}
}

def reset_daily_goals():
    for key in daily_goals:
        daily_goals[key]["count"] = 0
        if "minutes" in daily_goals[key]:
            daily_goals[key]["minutes"] = 0
    data["last_reset"] = datetime.now().strftime("%Y-%m-%d")
    save_data()

def get_level_name(score):
    if score >= 250:
        return "Чемпион семьи 🏆"
    elif score >= 150:
        return "Супергерой 💪"
    elif score >= 80:
        return "Ответственный 🎖"
    elif score >= 30:
        return "Помощник ✨"
    else:
        return "Новичок 👶"

def check_level_up(message, old_score, new_score):
    old_level = get_level_name(old_score)
    new_level = get_level_name(new_score)
    if old_level != new_level:
        bot.reply_to(message, f"🎉 Поздравляю! Ты достиг уровня: {new_level}")

def check_daily_goals(message):
    today = datetime.now().strftime("%Y-%m-%d")
    goals_met = True

    if daily_goals["чистка зубов"]["count"] < 2:
        goals_met = False
    if daily_goals["застелить постель"]["count"] < 1:
        goals_met = False
    if daily_goals["чтение"]["minutes"] < 30:
        goals_met = False
    if daily_goals["прогулка на улице"]["minutes"] < 30:
        goals_met = False

    if goals_met:
        reward_minutes = int(daily_goals["чтение"]["minutes"] * 2)
        data["log"][today] = {"completed": True, "reward_minutes": reward_minutes}
        bot.reply_to(message, f"🎉 Ура! Все цели дня выполнены! Ты получаешь {reward_minutes} минут на телефоне!")
    else:
        data["log"][today] = {"completed": False, "reward_minutes": 0}

    save_data()
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("📋 Задания")
    btn2 = types.KeyboardButton("✅ Выполнено")
    btn3 = types.KeyboardButton("📈 Баланс")
    btn4 = types.KeyboardButton("🏆 Рейтинг")
    btn5 = types.KeyboardButton("📅 Прогресс")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5)
    bot.send_message(message.chat.id, "Привет! Выбери, что хочешь сделать 👇", reply_markup=markup)

@bot.message_handler(commands=['задания'])
def show_tasks(message):
    if not data["tasks"]:
        bot.reply_to(message, "Заданий пока нет. Родитель может их добавить.")
    else:
        response = "Вот твои задания:\n"
        for task, points in data["tasks"].items():
            response += f"– {task} ({points} баллов)\n"
        bot.reply_to(message, response)

@bot.message_handler(commands=['баланс'])
def show_balance(message):
    bot.reply_to(message, f"У тебя {data['balance']} баллов")

@bot.message_handler(commands=['рейтинг'])
def show_rating(message):
    if not data.get("stats"):
        bot.reply_to(message, "Пока нет статистики.")
        return

    sorted_tasks = sorted(data["stats"].items(), key=lambda x: x[1]["points"], reverse=True)
    response = "📊 Рейтинг заданий:\n"
    for i, (task, stat) in enumerate(sorted_tasks, 1):
        response += f"{i}. {task.title()} — {stat['count']} раз ({stat['points']} баллов)\n"
    bot.reply_to(message, response)

@bot.message_handler(commands=['прогресс'])
def show_progress(message):
    log = data.get("log", {})
    if not log:
        bot.reply_to(message, "Пока нет прогресса.")
        return

    days = list(log.items())[-7:]  # последние 7 дней
    response = "📅 Прогресс за последние дни:\n"
    for date_str, info in days:
        mark = "✅" if info["completed"] else "❌"
        response += f"{date_str}: {mark}  ({info['reward_minutes']} мин)\n"
    bot.reply_to(message, response)
  @bot.message_handler(commands=['выполнено'])
def mark_done(message):
    if data.get("last_reset") != datetime.now().strftime("%Y-%m-%d"):
        reset_daily_goals()

    args = message.text.replace('/выполнено', '').strip().lower().split()
    if not args:
        bot.reply_to(message, "Напиши задание. Например: /выполнено чтение 30")
        return

    task = args[0]
    minutes = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    time_based = {
        "чтение": 0.15,
        "английский язык": 0.2,
        "спорт": 0.13,
        "прогулка на улице": 0.13
    }

    if task in data["tasks"]:
        if task in time_based and minutes:
            points = round(minutes * time_based[task])
            if task in daily_goals:
                daily_goals[task]["minutes"] += minutes
        else:
            points = data["tasks"][task]
            if task in daily_goals and "count" in daily_goals[task]:
                daily_goals[task]["count"] += 1

        old_score = data["balance"]
        data["balance"] += points
        check_level_up(message, old_score, data["balance"])

        # статистика
        if task not in data["stats"]:
            data["stats"][task] = {"count": 0, "points": 0}
        data["stats"][task]["count"] += 1
        data["stats"][task]["points"] += points

        # лог
        timestamp = datetime.now().strftime("%H:%M")
        entry = f"{timestamp} — {message.from_user.first_name}: {task} (+{points})"
        data["actions"].append(entry)
        if str(message.from_user.id) != str(parent_id):
            bot.send_message(parent_id, f"📝 Действие: {entry}")

        save_data()
        bot.reply_to(message, f"Молодец! +{points} баллов. Баланс: {data['balance']}")

        check_daily_goals(message)
    else:
        bot.reply_to(message, "Такого задания нет. Проверь /задания")

@bot.message_handler(commands=['лог'])
def show_log(message):
    if str(message.from_user.id) != str(parent_id):
        bot.reply_to(message, "Эта команда доступна только родителю.")
        return
    log = data.get("actions", [])
    if not log:
        bot.reply_to(message, "Лог пуст.")
    else:
        response = "\n".join(log[-10:])
        bot.reply_to(message, f"📋 Последние действия:\n{response}")

# Кнопки (главное меню)
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    text = message.text.strip()

    if text == "📋 Задания":
        show_tasks(message)
    elif text == "✅ Выполнено":
        bot.send_message(message.chat.id, "Напиши, что ты выполнил, например: выполнено чтение 30")
    elif text == "📈 Баланс":
        show_balance(message)
    elif text == "🏆 Рейтинг":
        show_rating(message)
    elif text == "📅 Прогресс":
        show_progress(message)
    else:
        bot.send_message(message.chat.id, "Я не понял 🤖 Выберите действие из меню.")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)
