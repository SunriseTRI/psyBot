import sqlite3

class DBHelper:
    def __init__(self, db_path='psybot.db'):
        self.db_path = db_path
        self.create_tables()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def create_tables(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS unanswered_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question TEXT
        )""")
        conn.commit()
        conn.close()

    def add_unanswered_question(self, user_id, question):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO unanswered_questions (user_id, question) VALUES (?, ?)",
            (user_id, question)
        )
        conn.commit()
        conn.close()

    def fetch_unanswered_questions(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM unanswered_questions")
        results = cursor.fetchall()
        conn.close()
        return results
