import sqlite3
import telebot
import re
import random
import string
from transformers import DistilBertTokenizer, DistilBertForQuestionAnswering
import torch

# Инициализация бота
API_TOKEN = '7425361233:AAHLhNWDrND8gfwXzS6IFrIhWvmMfFna0aY'
bot = telebot.TeleBot(API_TOKEN)

# Подключение к базе данных
def connect_db():
    conn = sqlite3.connect('psybot.db')
    cursor = conn.cursor()
    return conn, cursor

# Создание базы данных и таблиц
def create_db():
    conn, cursor = connect_db()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        name TEXT,
        surname TEXT,
        age INTEGER,
        phone TEXT,
        email TEXT,
        user_type TEXT,
        password TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faq (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        answer TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faqunanswered (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        added_by TEXT
    )""")
    conn.commit()
    conn.close()

create_db()

# Заполнение FAQ стандартными вопросами
def populate_standard_faq():
    conn, cursor = connect_db()
    standard_questions = [
        ("Как записаться на консультацию?", "Свяжитесь с нами через раздел регистрации."),
        ("Что делать, если я не могу прийти на консультацию?", "Пожалуйста, отмените запись через календарь."),
        # ... (добавьте ещё 28 стандартных вопросов)
    ]
    cursor.executemany("INSERT INTO faq (question, answer) VALUES (?, ?)", standard_questions)
    conn.commit()
    conn.close()

populate_standard_faq()

# Генерация случайного пароля
def generate_password(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Валидация номера телефона
def validate_phone(phone):
    pattern = r'^\+?\d{10,15}$'
    return re.match(pattern, phone) is not None

# Валидация email
def validate_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

# Состояние для регистрации
user_registration = {}

@bot.message_handler(commands=['reg'])
def start_registration(message):
    username = message.from_user.username
    conn, cursor = connect_db()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user:
        bot.reply_to(message, "Вы уже зарегистрированы!")
    else:
        user_registration[message.chat.id] = {'username': username}
        bot.reply_to(message, "Как вас зовут? (Имя)")

@bot.message_handler(func=lambda message: message.chat.id in user_registration)
def handle_registration(message):
    user_data = user_registration[message.chat.id]

    if 'name' not in user_data:
        user_data['name'] = message.text.strip()
        bot.reply_to(message, "Какая у вас фамилия? (Фамилия)")
    elif 'surname' not in user_data:
        user_data['surname'] = message.text.strip()
        bot.reply_to(message, "Сколько вам лет? (Возраст)")
    elif 'age' not in user_data:
        if message.text.isdigit() and 0 < int(message.text) < 120:
            user_data['age'] = int(message.text)
            bot.reply_to(message, "Введите ваш номер телефона (в формате +1234567890):")
        else:
            bot.reply_to(message, "Введите корректный возраст!")
    elif 'phone' not in user_data:
        if validate_phone(message.text.strip()):
            user_data['phone'] = message.text.strip()
            bot.reply_to(message, "Введите ваш email:")
        else:
            bot.reply_to(message, "Введите корректный номер телефона!")
    elif 'email' not in user_data:
        if validate_email(message.text.strip()):
            user_data['email'] = message.text.strip()
            bot.reply_to(message, "Выберите тип пользователя (patient, worker, admin, creator):")
        else:
            bot.reply_to(message, "Введите корректный email!")
    elif 'user_type' not in user_data:
        user_data['user_type'] = message.text.strip()
        user_data['password'] = generate_password()

        conn, cursor = connect_db()
        cursor.execute("""
        INSERT INTO users (username, name, surname, age, phone, email, user_type, password)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_data['username'],
            user_data['name'],
            user_data['surname'],
            user_data['age'],
            user_data['phone'],
            user_data['email'],
            user_data['user_type'],
            user_data['password']
        ))
        conn.commit()
        conn.close()

        bot.reply_to(message, f"Вы успешно зарегистрированы!\nВаш пароль: {user_data['password']}")
        user_registration.pop(message.chat.id)

# Модель обработки вопросов
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
model = DistilBertForQuestionAnswering.from_pretrained('distilbert-base-uncased')

def get_answer_from_model(question, context):
    inputs = tokenizer(question, context, return_tensors='pt')
    with torch.no_grad():
        outputs = model(**inputs)
    answer_start = torch.argmax(outputs.start_logits)
    answer_end = torch.argmax(outputs.end_logits) + 1
    answer = tokenizer.convert_tokens_to_string(
        tokenizer.convert_ids_to_tokens(inputs.input_ids[0][answer_start:answer_end]))
    return answer

@bot.message_handler(func=lambda message: True)
def handle_general_message(message):
    username = message.from_user.username
    conn, cursor = connect_db()
    cursor.execute("SELECT user_type FROM users WHERE username = ?", (username,))
    user_type = cursor.fetchone()[0] if cursor.fetchone() else None
    conn.close()

    context = "Ваш предопределённый контекст."
    answer = get_answer_from_model(message.text, context)

    if not answer or "[CLS]" in answer:
        if user_type in ['patient', 'worker']:
            bot.reply_to(message, "Я пока не знаю ответа на этот вопрос, но записал его для дальнейшего изучения.")
        elif user_type in ['admin', 'creator']:
            bot.reply_to(message, "Не могу ответить на этот вопрос. Хотите: 1) Внести ответ или 2) Добавить в список?")
        conn, cursor = connect_db()
        cursor.execute("INSERT INTO faqunanswered (question, added_by) VALUES (?, ?)", (message.text, username))
        conn.commit()
        conn.close()
    else:
        bot.reply_to(message, answer)

# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
