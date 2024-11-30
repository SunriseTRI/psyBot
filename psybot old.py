import telebot
from telebot import types
import re
import sqlite3
from nlp_utils import get_answer
import sqlite3


def create_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Удалить таблицу, если она существует
    cursor.execute("DROP TABLE IF EXISTS users")

    # Создание таблицы с правильной схемой
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (name TEXT, surname TEXT, age INTEGER, phone TEXT, email TEXT, user_type TEXT, password TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS faq
                      (question TEXT, answer TEXT)''')

    # Заполнение таблицы FAQ стандартными вопросами и ответами
    cursor.execute("INSERT OR REPLACE INTO faq (question, answer) VALUES (?, ?)",
                   ("привет", "Привет! Чем могу помочь?"))
    cursor.execute("INSERT OR REPLACE INTO faq (question, answer) VALUES (?, ?)",
                   ("что ты можешь",
                    "Я могу помочь тебе зарегистрироваться, ответить на вопросы и помочь с консультациями."))
    cursor.execute("INSERT OR REPLACE INTO faq (question, answer) VALUES (?, ?)",
                   ("кто ты",
                    "Я бот-помощник, который помогает с регистрацией и вопросами, связанными с психотерапией."))
    cursor.execute("INSERT OR REPLACE INTO faq (question, answer) VALUES (?, ?)",
                   ("пока", "До свидания! Если понадоблюсь — я всегда здесь."))
    cursor.execute("INSERT OR REPLACE INTO faq (question, answer) VALUES (?, ?)",
                   ("Как связаться с психологом?", "Контакты психолога указаны в вашем профиле."))
    cursor.execute("INSERT OR REPLACE INTO faq (question, answer) VALUES (?, ?)",
                   ("Как записаться на консультацию?",
                    "Вы можете записаться на консультацию, отправив запрос /appointment и выбрав психолога."))

    cursor.execute("INSERT OR REPLACE INTO faq (question, answer) VALUES (?, ?)",
                   ("Что делать, если я хочу отменить консультацию?",
                    "Консультацию можно отменить не позднее чем за 12 часов до назначенного времени."))

    # Создание записей пользователей
    # Пример данных для пользователей
    cursor.execute(
        "INSERT INTO users (name, surname, age, phone, email, user_type, password) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Иван", "Иванов", 30, "+79853834090", "ivanov@example.com", "user", None))
    cursor.execute(
        "INSERT INTO users (name, surname, age, phone, email, user_type, password) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Анна", "Петрова", 35, "+79853834091", "petrova@example.com", "worker", None))
    cursor.execute(
        "INSERT INTO users (name, surname, age, phone, email, user_type, password) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Сергей", "Сергеев", 40, "+79853834092", "sergeev@example.com", "admin", "adminpass"))
    cursor.execute(
        "INSERT INTO users (name, surname, age, phone, email, user_type, password) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Мария", "Смирнова", 45, "+79853834093", "smirnova@example.com", "creator", "creatorpass"))

    # Сохранение изменений и закрытие соединения
    conn.commit()
    conn.close()
    conn.close()


create_db()

bot = telebot.TeleBot('7425361233:AAHLhNWDrND8gfwXzS6IFrIhWvmMfFna0aY')

name = ''
surname = ''
age = 0
phone = ''
email = ''


@bot.message_handler(func=lambda message: True)
def respond_to_general_questions(message):
    text = message.text.lower()
    cursor.execute("SELECT question, answer FROM faq")
    faq_data = cursor.fetchall()

    # Объединяем все ответы в общий контекст
    context = "\n".join([f"Q: {row[0]} A: {row[1]}" for row in faq_data])

    # Получаем ответ на основе контекста
    answer = get_answer(text, context)

    if answer:
        bot.reply_to(message, answer)
    else:
        bot.reply_to(message, "Извините, я пока не знаю ответа на этот вопрос.")


def get_name(message):
    global name
    name = message.text
    bot.send_message(message.chat.id, "Какая у тебя фамилия?")
    bot.register_next_step_handler(message, get_surname)


def get_surname(message):
    global surname
    surname = message.text
    bot.send_message(message.chat.id, "Сколько тебе лет?")
    bot.register_next_step_handler(message, get_age)


def get_age(message):
    global age
    try:
        age = int(message.text)
        bot.send_message(message.chat.id, "Теперь, пожалуйста, укажи свой номер телефона в формате +7xxxxxxxxxx.")
        bot.register_next_step_handler(message, get_phone)
    except ValueError:
        bot.send_message(message.chat.id, "Цифрами, пожалуйста. Сколько тебе лет?")
        bot.register_next_step_handler(message, get_age)


def get_phone(message):
    global phone
    phone = message.text
    if not re.match(r"^\+7\d{10}$", phone):
        bot.send_message(message.chat.id, "Номер телефона должен быть в формате +7xxxxxxxxxx. Попробуй еще раз.")
        bot.register_next_step_handler(message, get_phone)
    else:
        bot.send_message(message.chat.id, "Теперь, пожалуйста, укажи свою электронную почту.")
        bot.register_next_step_handler(message, get_email)


def get_email(message):
    global email
    email = message.text
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        bot.send_message(message.chat.id, "Некорректный email. Попробуй еще раз.")
        bot.register_next_step_handler(message, get_email)
    else:

        confirmation_message = (
            f"Тебе {age} лет,\n"
            f"Тебя зовут {name} {surname},\n"
            f"Твой №телефона: {phone},\n"
            f"Твой email: {email}\n"
            f"Всё верно?"
        )
        keyboard = types.InlineKeyboardMarkup()
        key_yes = types.InlineKeyboardButton(text="Да", callback_data="yes")
        key_no = types.InlineKeyboardButton(text="Нет", callback_data="no")
        keyboard.add(key_yes, key_no)
        bot.send_message(message.chat.id, confirmation_message, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data == "yes":
        # Сохранение данных в базу данных
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, surname, age, phone, email) VALUES (?, ?, ?, ?, ?)",
                       (name, surname, age, phone, email))
        conn.commit()
        conn.close()
        bot.send_message(call.message.chat.id, 'Спасибо за регистрацию! Все данные сохранены.')
    elif call.data == "no":
        bot.send_message(call.message.chat.id, 'Давайте попробуем еще раз.')
        start_registration(call.message)

    @bot.message_handler(func=lambda message: True)
    def respond_to_general_questions(message):
        text = message.text.lower()

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT answer FROM faq WHERE question=?", (text,))
        result = cursor.fetchone()
        conn.close()

        if result:
            bot.send_message(message.chat.id, result[0])
        else:
            bot.send_message(message.chat.id,
                             "Я не совсем понимаю твой вопрос. Попробуй задать что-то другое или напиши /help.")


bot.polling(none_stop=True, interval=0)
