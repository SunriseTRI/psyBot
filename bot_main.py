import telebot
from db_helper import DBHelper
from transformers_helper import get_answer_from_model

# Инициализация бота
API_TOKEN = '7425361233:AAHLhNWDrND8gfwXzS6IFrIhWvmMfFna0aY'
bot = telebot.TeleBot(API_TOKEN)

# Инициализация помощников
db = DBHelper()

# Команды бота
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я бот для помощи в психологии.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_question = message.text
    context = "Это контекст для моделей ответа."
    answer = get_answer_from_model(user_question, context)

    if answer:
        bot.reply_to(message, answer)
    else:
        bot.reply_to(message, "Не нашёл ответа. Запишу вопрос для анализа.")
        db.add_unanswered_question(message.chat.id, user_question)

if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True)
