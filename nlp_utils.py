from transformers import pipeline

# Инициализация модели для анализа
qa_pipeline = pipeline("question-answering", model="distilbert-base-uncased", tokenizer="distilbert-base-uncased")

# Ответ на вопрос на основе текста
def get_answer(question, context):
    try:
        result = qa_pipeline(question=question, context=context)
        return result['answer']
    except Exception as e:
        return f"Извините, не удалось обработать запрос: {str(e)}"
