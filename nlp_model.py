import csv
import logging
import torch
from transformers import DistilBertTokenizer, DistilBertForQuestionAnswering, Trainer, TrainingArguments
from datasets import Dataset
from database import get_faq
import pandas as pd

logging.basicConfig(level=logging.INFO)


tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-multilingual-cased')
model = DistilBertForQuestionAnswering.from_pretrained('distilbert-base-multilingual-cased')


def save_faq_to_csv(faq_rows, filename='faq_data.csv'):
    """Сохранение данных FAQ в CSV файл."""
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['question', 'answer'])  # Заголовки столбцов
        for row in faq_rows:
            writer.writerow([row[0], row[1]])  # Письмо вопроса и ответа
    logging.info(f"FAQ сохранены в файл {filename}")


def encode_data(question, answer):
    encoding = tokenizer(question, answer, padding=True, truncation=True, return_tensors="pt", max_length=512)

    if encoding['input_ids'].shape[1] != 512:
        logging.warning(
            f"Длина последовательности для вопроса '{question}' и ответа '{answer}' отличается от 512. Длина: {encoding['input_ids'].shape[1]}")

    inputs = {key: val for key, val in encoding.items() if key in ['input_ids', 'attention_mask']}
    return inputs


def get_answer_from_model(question, context):
    try:
        inputs = tokenizer(question, context, return_tensors='pt')
        with torch.no_grad():
            outputs = model(**inputs)
        start = torch.argmax(outputs.start_logits)
        end = torch.argmax(outputs.end_logits) + 1
        answer = tokenizer.convert_tokens_to_string(
            tokenizer.convert_ids_to_tokens(inputs.input_ids[0][start:end])
        )
        logging.info(f"Ответ от модели: {answer}")
        return answer
    except Exception as e:
        logging.error(f"Ошибка в обработке вопроса: {e}")
        return None


def train_model(faq_data):

    if faq_data.empty:
        logging.error("Данные FAQ пусты. Обучение не может быть выполнено.")
        return

    try:
        train_data = faq_data.apply(lambda row: encode_data(row['question'], row['answer']), axis=1).tolist()
        logging.info("Токенизация данных завершена успешно.")
    except Exception as e:
        logging.error(f"Ошибка в токенизации данных: {e}")
        return

    train_dataset = Dataset.from_list(train_data)

    training_args = TrainingArguments(
        output_dir='./results',
        num_train_epochs=3,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=16,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir='./logs',
    )


    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
    )


    try:
        trainer.train()
    except Exception as e:
        logging.error(f"Ошибка при обучении модели: {e}")



faq_rows = get_faq()
save_faq_to_csv(faq_rows)


faq_df = pd.read_csv('faq_data.csv')


if faq_df.empty:
    logging.error("Файл faq_data.csv пуст. Обучение невозможно.")
else:
    train_model(faq_df)
