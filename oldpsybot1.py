import sqlite3
import telebot
import re
import random
import string
from transformers import DistilBertTokenizer, DistilBertForQuestionAnswering
import torch
import os
from datasets import load_dataset

dataset = load_dataset("squad")

# Отключение oneDNN
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
# Инициализация бота
API_TOKEN = '7425361233:AAHLhNWDrND8gfwXzS6IFrIhWvmMfFna0aY'
bot = telebot.TeleBot(API_TOKEN)

# Путь к базе данных
DB_PATH = 'psybot.db'

# Подключение к базе данных
def connect_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    return conn, cursor

# Создание базы данных и таблиц, если их нет
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

# NLP модель
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
model = DistilBertForQuestionAnswering.from_pretrained('distilbert-base-uncased')

def get_answer_from_model(question, context):
    inputs = tokenizer(question, context, return_tensors='pt')
    with torch.no_grad():
        outputs = model(**inputs)
    start = torch.argmax(outputs.start_logits)
    end = torch.argmax(outputs.end_logits) + 1
    return tokenizer.convert_tokens_to_string(
        tokenizer.convert_ids_to_tokens(inputs.input_ids[0][start:end]))

# Регистрация пользователей
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

        bot.reply_to(message, f"Регистрация завершена!\nВаш пароль: {user_data['password']}")
        user_registration.pop(message.chat.id)

# # Модель для обработки вопросов
# tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
# model = DistilBertForQuestionAnswering.from_pretrained('distilbert-base-uncased')
#
# # Получение ответа с использованием модели
# def get_answer_from_model(question, context):
#     inputs = tokenizer(question, context, return_tensors='pt')
#     with torch.no_grad():
#         outputs = model(**inputs)
#     answer_start = torch.argmax(outputs.start_logits)
#     answer_end = torch.argmax(outputs.end_logits) + 1
#     answer = tokenizer.convert_tokens_to_string(
#         tokenizer.convert_ids_to_tokens(inputs.input_ids[0][answer_start:answer_end]))
#     return answer

@bot.message_handler(func=lambda message: message.text.lower() == "faq")
def respond_to_faq(message):
    conn, cursor = connect_db()
    cursor.execute("SELECT question, answer FROM faq")
    rows = cursor.fetchall()

    if rows:
        response = "\n\n".join([f"Q: {row[0]}\nA: {row[1]}" for row in rows])
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "FAQ пока пуст.")
    conn.close()

@bot.message_handler(func=lambda message: True)
def handle_general_message(message):
    username = message.from_user.username
    conn, cursor = connect_db()
    cursor.execute("SELECT user_type FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    user_type = result[0] if result else None
    context = "Ваш предопределённый контекст."
    answer = get_answer_from_model(message.text, context)

    if not answer or "[CLS]" in answer:
        bot.reply_to(message, "Не могу ответить на этот вопрос. Он добавлен для дальнейшей обработки.")
        conn, cursor = connect_db()
        cursor.execute("INSERT INTO faqunanswered (question, added_by) VALUES (?, ?)", (message.text, username))
        conn.commit()
        conn.close()
    else:
        bot.reply_to(message, answer)


def get_user_type(user_id):
    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        cursor.execute("SELECT user_type FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Ошибка при работе с базой данных: {e}")
        return None
    finally:
        connection.close()













###########################################################################################!!
# Заполнение FAQ стандартными вопросами
def populate_standard_faq():
    conn, cursor = connect_db()
    standard_questions = [
        ("привет", "Привет псих."),
        ("Как записаться на консультацию?", "Свяжитесь с нами через раздел регистрации."),
        ("Что делать, если я не могу прийти на консультацию?", "Пожалуйста, отмените запись через календарь."),
        ("Как изменить дату консультации?", "Вы можете переназначить дату консультации через личный кабинет."),
        ("Как удалить свою учетную запись?", "Для удаления учетной записи свяжитесь с нами через поддержку."),
        ("Какие способы оплаты доступны?", "Вы можете оплатить через банковскую карту или электронные кошельки."),
        ("Какие консультации предоставляются?",
         "Мы предоставляем консультации по психологии, психотерапии и личностному росту."),
        ("Сколько стоит консультация?", "Стоимость консультации зависит от типа и длительности встречи."),
        ("Как узнать расписание консультантов?", "Вы можете узнать расписание в разделе 'Календарь' на сайте."),
        ("Есть ли скидки на консультации?", "Да, для постоянных клиентов предусмотрены скидки."),
        ("Как изменить личные данные?", "Вы можете изменить свои данные в разделе 'Личный кабинет'."),
        ("Как подтвердить свою запись на консультацию?",
         "После записи на консультацию, вы получите подтверждение по e-mail."),
        ("Как отменить запись?", "Вы можете отменить запись через раздел 'Мои консультации' в личном кабинете."),
        ("Как записаться на консультацию для другого человека?",
         "Для записи другого человека, укажите его данные в разделе 'Регистрация' на сайте."),
        ("Что делать, если я не могу найти подходящего психолога?",
         "Вы можете выбрать другого специалиста в разделе 'Все психологи'."),
        ("Какие виды терапии вы предлагаете?",
         "Мы предлагаем когнитивно-поведенческую терапию, гештальт-терапию и другие методы."),
        ("Можно ли выбрать конкретного психолога?",
         "Да, вы можете выбрать психолога, ориентируясь на их специализацию и опыт."),
        ("Какие у вас есть сертификаты и лицензии?",
         "Наши специалисты имеют соответствующие дипломы и сертификаты."),
        ("Как узнать отзывы о психологах?", "Отзывы можно найти на профиле каждого специалиста."),
        ("Что делать, если я не доволен консультацией?",
         "Если вы не удовлетворены консультацией, сообщите об этом в нашу поддержку."),
        ("Как часто нужно посещать психолога?", "Частота встреч зависит от ваших личных целей и ситуации."),
        ("Что делать, если я не могу заплатить за консультацию?",
         "Мы предлагаем рассрочку и скидки для нуждающихся."),
        ("Какие документы нужны для записи?",
         "Для записи достаточно указать ваше имя, возраст и контактные данные."),
        ("Как записаться на консультацию с группой?",
         "Для записи на групповую консультацию, свяжитесь с нами по телефону."),
        ("Есть ли возможность консультации по видеосвязи?",
         "Да, мы предлагаем онлайн-консультации через видеосвязь."),
        ("Как мне задать вопрос консультанту до встречи?",
         "Вы можете отправить свой вопрос через чат в личном кабинете."),
        ("Как узнать, когда откроется запись на следующую консультацию?",
         "Вы получите уведомление по e-mail, когда будет открыта запись."),
        ("Что делать, если я пропустил консультацию?", "Вы можете перенести консультацию или записаться заново."),
        ("Можно ли получить консультацию анонимно?", "Да, при регистрации можно указать анонимные данные."),
        ("Как изменить тип консультации?",
         "Вы можете изменить тип консультации в разделе 'Мои консультации' в личном кабинете."),
        ("Как выбрать подходящего психолога?",
         "Вы можете фильтровать психологов по специализациям, опыту и отзывам."),
        ("Могу ли я получить консультацию для пары?", "Да, мы предлагаем консультации для пар."),
        ("Как долго длится консультация?", "Обычно консультации длятся от 45 минут до 1 часа."),
        ("Какие психотерапевтические подходы вы используете?",
         "Мы используем различные подходы, включая когнитивно-поведенческую терапию и гештальт-терапию."),
        ("Могу ли я записаться на консультацию без регистрации?",
         "Нет, для записи необходимо создать учетную запись."),
        ("Как долго я буду ждать ответ на свой запрос?", "Ответ обычно приходит в течение 1-2 рабочих дней."),
        ("Какие документы нужно предоставить для первой консультации?",
         "Для первой консультации достаточно паспорта или другого удостоверяющего личность документа."),
        ("Как узнать стоимость консультации?", "Вы можете узнать стоимость на странице выбранного психолога."),
        ("Какие способы связи с психологом вы используете?",
         "Мы используем видеосвязь, телефонные консультации и чат."),
        ("Что делать, если я не могу найти свой вопрос в FAQ?",
         "Если ваш вопрос не найден, напишите его нам, и мы ответим."),
        ("Можно ли записаться на консультацию по выходным?",
         "Да, многие психологи доступны для консультаций по выходным."),
        ("Что делать, если я забыл свой пароль?",
         "Вы можете восстановить пароль через функцию 'Забыли пароль?' на странице входа."),
        ("Как я могу изменить время своей консультации?",
         "Вы можете переназначить консультацию через личный кабинет."),
        ("Можно ли записаться на несколько консультаций сразу?",
         "Да, вы можете записаться на несколько консультаций через календарь."),
        ("Как мне связаться с поддержкой?", "Вы можете связаться с нами через чат на сайте или по телефону."),
        ("Какие психологи доступны для консультации онлайн?",
         "Вы можете выбрать психологов, предлагающих онлайн-консультации в фильтре на сайте."),
        ("Как записаться на консультацию, если я не знаю, кто мне подходит?",
         "Вы можете выбрать психолога, основываясь на его специализации или записаться на консультацию без выбора."),
        ("Есть ли у вас бесплатные консультации?",
         "Мы предлагаем бесплатную первую консультацию для новых клиентов."),
        ("Как долго можно получать консультации?",
         "Продолжительность консультаций зависит от ваших целей и предпочтений."),
        ("Как записаться на консультацию по телефону?",
         "Вы можете записаться на консультацию по телефону, позвонив нам."),
        ("Можно ли получить консультацию в выходные или праздничные дни?",
         "Да, мы работаем в выходные и праздничные дни."),
        ("Как зарегистрироваться на консультацию?", "Для регистрации перейдите в раздел 'Регистрация' на сайте."),
        ("Какие у вас есть услуги для детей?",
         "Мы предлагаем консультации для детей и подростков, используя специальные методики."),
        ("Как я могу оставить отзыв о консультации?",
         "После консультации вы получите ссылку для оставления отзыва."),
        ("Что делать, если я хочу изменить психолога?",
         "Вы можете выбрать другого психолога в разделе 'Все психологи' на сайте."),
        (
            "Можно ли получать консультации анонимно?", "Да, вы можете скрыть свои данные при записи на консультацию."),
        ("Как изменить личные данные в учетной записи?", "Вы можете изменить данные через личный кабинет."),
        ("Как мне узнать, когда будет доступен мой психолог?",
         "Вы можете узнать расписание выбранного психолога через календарь на сайте."),
        (
            "Что делать, если консультация отменена?", "Вы получите уведомление, и можете переназначить консультацию."),
        ("Как часто нужно ходить на консультации?", "Частота консультаций зависит от вашей ситуации и целей."),
        ("Какие психологи доступны для консультации по семейным вопросам?",
         "Вы можете выбрать психолога с опытом работы с семейными проблемами."),
        ("Как отменить консультацию?", "Вы можете отменить консультацию через личный кабинет."),
        ("Есть ли у вас психологи для людей с депрессией?",
         "Да, у нас есть психологи, специализирующиеся на депрессиях и тревожных расстройствах."),
        ("Как мне получить помощь по телефону?", "Позвоните нам по номеру, указанному на сайте."),
        ("Как выбрать психолога по специализации?",
         "Вы можете фильтровать психологов по специализациям через поисковую систему на сайте."),
        ("Как записаться на консультацию с психотерапевтом?",
         "Для записи на консультацию с психотерапевтом свяжитесь с нами напрямую."),
        ("Как мне связаться с администратором?", "Вы можете связаться с администратором через чат на сайте."),
        ("Как я могу отменить запись на консультацию?",
         "Запись можно отменить в разделе 'Мои консультации' в личном кабинете."),
        ("Что делать, если я не могу оплатить консультацию?",
         "Свяжитесь с нами, чтобы обсудить возможность рассрочки или скидки."),
        ("Как записаться на консультацию, если я не из вашего города?",
         "Вы можете записаться на онлайн-консультацию через видеосвязь."),
        ("Как узнать, когда будет следующий прием у психолога?",
         "Вы можете узнать дату следующего приема через календарь на сайте."),
        ("Как мне получить информацию о скидках?",
         "Вы можете узнать о скидках на странице 'Скидки' на нашем сайте."),
        ("Как записаться на консультацию с психиатром?",
         "Для записи на консультацию с психиатром свяжитесь с нами напрямую."),
    ]
    cursor.executemany("INSERT INTO faq (question, answer) VALUES (?, ?)", standard_questions)
    conn.commit()
    conn.close()

populate_standard_faq()


# Запуск бота
if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True, interval=0)


