import sqlite3
import telebot
from transformers import DistilBertTokenizer, DistilBertForQuestionAnswering
import torch

# Инициализация бота
API_TOKEN = ''7425361233:AAHLhNWDrND8gfwXzS6IFrIhWvmMfFna0aY''
bot = telebot.TeleBot(API_TOKEN)


# Подключение к базе данных
# Функция для подключения к базе данных
def connect_db():
    conn = sqlite3.connect('psybot.db')
    cursor = conn.cursor()
    return conn, cursor


# создания базы данных и таблиц, если их нет
def create_db():
    conn, cursor = connect_db()

    # пользователи
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        surname TEXT,
        age INTEGER,
        phone TEXT,
        email TEXT,
        user_type TEXT,
        password TEXT
    )""")

    # вопрос и ответ (FAQ)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faq (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        answer TEXT
    )""")

    conn.commit()
    conn.close()


create_db()

#обработка запросов от пользователей
def respond_to_general_questions(message):
    conn, cursor = connect_db()

    cursor.execute("SELECT question, answer FROM faq")
    rows = cursor.fetchall()

    for row in rows:
        question, answer = row
        bot.send_message(message.chat.id, f"Q: {question}\nA: {answer}")

    conn.close()


#  модели для обработки вопросов и ответов
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
model = DistilBertForQuestionAnswering.from_pretrained('distilbert-base-uncased')


# обработка вопросов с использованием модели
def get_answer_from_model(question, context):
    inputs = tokenizer(question, context, return_tensors='pt')
    with torch.no_grad():
        outputs = model(**inputs)
    answer_start = torch.argmax(outputs.start_logits)
    answer_end = torch.argmax(outputs.end_logits) + 1
    answer = tokenizer.convert_tokens_to_string(
        tokenizer.convert_ids_to_tokens(inputs.input_ids[0][answer_start:answer_end]))
    return answer


# обработка текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text.lower() == "faq":
        respond_to_general_questions(message)
    else:
        context = "Your predefined context goes here."  # Установите свой контекст
        answer = get_answer_from_model(message.text, context)
        bot.reply_to(message, answer)


# стартер если бочёк не потик
if __name__ == '__main__':
    create_db()  # Создание базы данных, если её ещё нет
    bot.polling(none_stop=True, interval=0)
