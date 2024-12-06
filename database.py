import sqlite3

DB_PATH = 'psybot.db'

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    return conn, cursor

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
def get_user_by_username(username):
    conn, cursor = connect_db()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def insert_user(user_data):
    conn, cursor = connect_db()
    cursor.execute("""
    INSERT INTO users (username, name, surname, age, phone, email, user_type, password)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, user_data)
    conn.commit()
    conn.close()

def get_faq():
    conn, cursor = connect_db()
    cursor.execute("SELECT question, answer FROM faq")
    rows = cursor.fetchall()
    conn.close()
    return rows

def insert_unanswered_question(question, added_by):
    conn, cursor = connect_db()
    cursor.execute("INSERT INTO faqunanswered (question, added_by) VALUES (?, ?)", (question, added_by))
    conn.commit()
    conn.close()



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
