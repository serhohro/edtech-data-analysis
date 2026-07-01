import pandas as pd
import os
import sys

# Настройка путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.append(BASE_DIR)

def clean_spend():
    # Загружаем файл
    # Поля Source и Campaign оставляем строками, чтобы не потерять кодировки
    spend = pd.read_excel('Spend (Done).xlsx')
    
    # Считаем строки ДО
    rows_before = len(spend)

    # 1. Очистка названий колонок от случайных пробелов
    spend.columns = [col.strip() for col in spend.columns]

    # 2. Преобразование дат (Критерий ТЗ №3)
    # В этом файле даты обычно без времени, но формат ISO (ГГГГ-ММ-ДД) идеален для связи таблиц
    spend['Date'] = pd.to_datetime(spend['Date'], dayfirst=True, errors='coerce')

    # 3. Обработка числовых данных
    # Если есть пустые значения в тратах или кликах, заменяем их на 0, чтобы формулы не ломались
    numeric_cols = ['Impressions', 'Clicks', 'Spend']
    for col in numeric_cols:
        if col in spend.columns:
            spend[col] = pd.to_numeric(spend[col], errors='coerce').fillna(0)

    # 4. Обработка текстовых полей
    # Заполняем пустые кампании или источники, чтобы они не выпадали из отчетов
    spend['Source'] = spend['Source'].fillna('Unknown')
    spend['Campaign'] = spend['Campaign'].fillna('Unknown')

    # 5. Удаление полных дублей
    spend = spend.drop_duplicates()
    
    # Считаем строки ПОСЛЕ
    rows_after = len(spend)

    # Сохраняем в CSV
    spend.to_csv('spend_cleaned.csv', index=False)

    print(f"Файл Spend готов. Обработано строк: {len(spend)}")
    
    # Возвращаем данные для отчета
    return {
        'File': 'Spend',
        'Before': rows_before,
        'After': rows_after,
        'Deleted': rows_before - rows_after,
        'Drop %': f"{(rows_before - rows_after) / rows_before:.1%}" if rows_before > 0 else "0%"
    }

if __name__ == "__main__":
    stats = clean_spend()
    print(f"Готово: {stats}")