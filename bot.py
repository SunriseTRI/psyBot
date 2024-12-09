import telebot
import random
import string
import re
from database import create_db, get_user_by_username, insert_user, get_faq, insert_unanswered_question
from nlp_model import get_answer_from_model
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
API_TOKEN = '7425361233:AAHLhNWDrND8gfwXzS6IFrIhWvmMfFna0aY'
bot = telebot.TeleBot(API_TOKEN)
create_db()
user_registration = {}
pending_messages = {}


def generate_password(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def validate_phone(phone):
    pattern = r'^\+?\d{10,15}$'
    return re.match(pattern, phone) is not None


def validate_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None


@bot.message_handler(commands=['reg'])
def start_registration(message):
    username = message.from_user.username
    user = get_user_by_username(username)

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

        user_data_tuple = (
            user_data['username'],
            user_data['name'],
            user_data['surname'],
            user_data['age'],
            user_data['phone'],
            user_data['email'],
            user_data['user_type'],
            user_data['password']
        )
        insert_user(user_data_tuple)

        bot.reply_to(message, f"Регистрация завершена!\nВаш пароль: {user_data['password']}")
        user_registration.pop(message.chat.id)

        # Если сообщение ожидает обработки, обрабатываем его
        if message.chat.id in pending_messages:
            handle_message(pending_messages.pop(message.chat.id))


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    username = message.from_user.username
    logging.info(f"Получено сообщение от {username}: {message.text}")

    user = get_user_by_username(username)
    if not user:
        bot.reply_to(message, "Пожалуйста, зарегистрируйтесь, используя команду /reg")
        pending_messages[message.chat.id] = message  # Сохраняем сообщение для обработки после регистрации
        logging.info(f"Пользователь {username} не зарегистрирован. Сообщение сохранено для дальнейшей обработки.")
        return

    rows = get_faq()
    exact_answer = next((row[1] for row in rows if row[0].lower() in message.text.lower()), None)

    if exact_answer:  # Если нашли точный ответ в FAQ
        bot.reply_to(message, exact_answer)
        logging.info(f"Ответ найден в FAQ для вопроса: {message.text}. Ответ: {exact_answer}")
    else:  # Если точного ответа нет, ищем похожие
        similar_questions = [row for row in rows if message.text.lower() in row[0].lower()]
        if similar_questions:
            options = "\n".join([f"{i+1}. {q[0]}" for i, q in enumerate(similar_questions)])
            bot.reply_to(message, f"Возможно, вы имели в виду:\n{options}\nНапишите номер подходящего вопроса или '0', если ничего не подходит.")
        else:
            # Если нет похожих вопросов, обращаемся к NLP модели
            answer = get_answer_from_model(message.text, message.text)
            if not answer or "[CLS]" in answer:
                bot.reply_to(message, "Не могу ответить на этот вопрос. Он добавлен для дальнейшей обработки.")
                insert_unanswered_question(message.text, username)
                logging.info(f"Ответ не найден. Вопрос добавлен для дальнейшей обработки: {message.text}")
            else:
                bot.reply_to(message, answer)
                logging.info(f"Ответ от модели: {answer}")


if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True, interval=0)
