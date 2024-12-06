import telebot  # Импорт библиотеки для работы с Telegram ботом
import random  # Импорт библиотеки для генерации случайных значений
import string  # Импорт библиотеки для работы со строками
import re  # Импорт библиотеки для работы с регулярными выражениями
from database import create_db, get_user_by_username, insert_user, get_faq, insert_unanswered_question  # Импорт функций для работы с базой данных
from nlp_model import get_answer_from_model  # Импорт функции для получения ответа от NLP модели

# Инициализация бота
API_TOKEN = '7425361233:AAHLhNWDrND8gfwXzS6IFrIhWvmMfFna0aY'  # Токен бота для авторизации
bot = telebot.TeleBot(API_TOKEN)  # Создание экземпляра бота с токеном

create_db()  # Создание базы данных (предполагается, что это создаёт нужную структуру БД)

user_registration = {}  # Хранилище данных пользователей, которые проходят регистрацию

# Генерация случайного пароля
def generate_password(length=6):  # Функция для генерации случайного пароля
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))  # Генерация пароля из букв и цифр

# Валидация номера телефона
def validate_phone(phone):  # Функция для проверки номера телефона
    pattern = r'^\+?\d{10,15}$'  # Регулярное выражение для номера телефона
    return re.match(pattern, phone) is not None  # Проверка соответствия шаблону

# Валидация email
def validate_email(email):  # Функция для проверки email
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'  # Регулярное выражение для email
    return re.match(pattern, email) is not None  # Проверка соответствия шаблону

@bot.message_handler(commands=['reg'])  # Обработчик команды /reg
def start_registration(message):  # Функция, которая запускает процесс регистрации
    username = message.from_user.username  # Получаем имя пользователя
    user = get_user_by_username(username)  # Проверяем, есть ли уже пользователь с таким именем

    if user:  # Если пользователь уже зарегистрирован
        bot.reply_to(message, "Вы уже зарегистрированы!")  # Сообщаем, что он уже зарегистрирован
    else:  # Если пользователя нет в базе
        user_registration[message.chat.id] = {'username': username}  # Начинаем процесс регистрации для текущего чата
        bot.reply_to(message, "Как вас зовут? (Имя)")  # Спрашиваем имя

@bot.message_handler(func=lambda message: message.chat.id in user_registration)  # Обработчик сообщений в процессе регистрации
def handle_registration(message):  # Функция обработки данных регистрации
    user_data = user_registration[message.chat.id]  # Получаем данные о пользователе, который регистрируется

    if 'name' not in user_data:  # Если имя еще не введено
        user_data['name'] = message.text.strip()  # Сохраняем имя
        bot.reply_to(message, "Какая у вас фамилия? (Фамилия)")  # Спрашиваем фамилию
    elif 'surname' not in user_data:  # Если фамилия не введена
        user_data['surname'] = message.text.strip()  # Сохраняем фамилию
        bot.reply_to(message, "Сколько вам лет? (Возраст)")  # Спрашиваем возраст
    elif 'age' not in user_data:  # Если возраст не введен
        if message.text.isdigit() and 0 < int(message.text) < 120:  # Проверяем, что введен корректный возраст
            user_data['age'] = int(message.text)  # Сохраняем возраст
            bot.reply_to(message, "Введите ваш номер телефона (в формате +1234567890):")  # Спрашиваем телефон
        else:  # Если возраст некорректный
            bot.reply_to(message, "Введите корректный возраст!")  # Сообщаем о неправильном возрасте
    elif 'phone' not in user_data:  # Если телефон не введен
        if validate_phone(message.text.strip()):  # Проверяем корректность телефона
            user_data['phone'] = message.text.strip()  # Сохраняем телефон
            bot.reply_to(message, "Введите ваш email:")  # Спрашиваем email
        else:  # Если телефон некорректный
            bot.reply_to(message, "Введите корректный номер телефона!")  # Сообщаем об ошибке
    elif 'email' not in user_data:  # Если email не введен
        if validate_email(message.text.strip()):  # Проверяем корректность email
            user_data['email'] = message.text.strip()  # Сохраняем email
            bot.reply_to(message, "Выберите тип пользователя (patient, worker, admin, creator):")  # Спрашиваем тип пользователя
        else:  # Если email некорректный
            bot.reply_to(message, "Введите корректный email!")  # Сообщаем об ошибке
    elif 'user_type' not in user_data:  # Если тип пользователя не выбран
        user_data['user_type'] = message.text.strip()  # Сохраняем тип пользователя
        user_data['password'] = generate_password()  # Генерируем пароль

        # Создаем кортеж с данными пользователя для сохранения в базе
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
        insert_user(user_data_tuple)  # Вставляем данные в базу данных

        bot.reply_to(message, f"Регистрация завершена!\nВаш пароль: {user_data['password']}")  # Сообщаем пользователю, что регистрация завершена
        user_registration.pop(message.chat.id)  # Убираем пользователя из процесса регистрации

@bot.message_handler(func=lambda message: message.text.lower() == "faq")  # Обработчик команды "faq"
def respond_to_faq(message):  # Функция для ответа на запрос FAQ
    rows = get_faq()  # Получаем список FAQ из базы данных
    if rows:  # Если есть вопросы и ответы
        response = "\n\n".join([f"Q: {row[0]}\nA: {row[1]}" for row in rows])  # Формируем строку с вопросами и ответами
        bot.reply_to(message, response)  # Отправляем пользователю список FAQ
    else:  # Если FAQ пуст
        bot.reply_to(message, "FAQ пока пуст.")  # Сообщаем, что FAQ пуст

@bot.message_handler(func=lambda message: True)  # Обработчик всех остальных сообщений
def handle_general_message(message):  # Функция обработки общих сообщений
    username = message.from_user.username  # Получаем имя пользователя
    user = get_user_by_username(username)  # Получаем данные пользователя из базы данных

    user_type = user[7] if user else None  # Получаем тип пользователя (например, admin, patient)
    context = message.text  # Используем текст сообщения как контекст для модели
    print(f"Вопрос: {message.text}, Контекст: {context}")  # Логируем вопрос и контекст

    answer = get_answer_from_model(message.text, context)  # Получаем ответ от модели

    print(f"Ответ модели: {answer}")  # Логируем ответ от модели

    if not answer or "[CLS]" in answer:  # Если ответ не был получен или ответ невалиден
        bot.reply_to(message, "Не могу ответить на этот вопрос. Он добавлен для дальнейшей обработки.")  # Сообщаем, что ответ не найден
        insert_unanswered_question(message.text, username)  # Добавляем вопрос в базу для дальнейшей обработки
    else:  # Если ответ был получен
        bot.reply_to(message, answer)  # Отправляем ответ пользователю

# Запуск бота
if __name__ == "__main__":  # Если этот файл запущен напрямую
    print("Бот запущен...")  # Выводим сообщение, что бот запущен
    bot.polling(none_stop=True, interval=0)  # Начинаем слушать сообщения, бот работает в режиме polling
