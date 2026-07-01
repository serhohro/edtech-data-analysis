import pandas as pd
import os
import sys

# Настройка путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.append(BASE_DIR)

def clean_calls():

    # Загружаем, фиксируя ID как строки
    calls = pd.read_excel('Calls (Done).xlsx', dtype={'Id': str, 'CONTACTID': str})
    
    # Считаем строки ДО
    rows_before = len(calls)

    # 1. Очистка названий колонок
    calls.columns = [col.strip() for col in calls.columns]

    # 2. Преобразование дат (с учетом dayfirst=True)
    calls['Call Start Time'] = pd.to_datetime(calls['Call Start Time'], dayfirst=True, errors='coerce')

    # 3. Обработка числовых данных (Длительность звонка)
    # Оставляем как есть, но заполняем пустые значения нулями
    # Заполняем пустые длительности нулем и переводим в целое число
    calls['Call Duration (in seconds)'] = calls['Call Duration (in seconds)'].fillna(0).astype(int)
    calls['Call Duration (in seconds)'] = pd.to_numeric(calls['Call Duration (in seconds)'], errors='coerce').fillna(0)

    # 4. Обработка статусов
    # Заполняем пустые значения статусов, чтобы не терять звонки в воронке
    calls['Call Status'] = calls['Call Status'].fillna('Not Answered')
    calls['Call Type'] = calls['Call Type'].fillna('Unknown')

    # 5. Обрабатываем значения в Scheduled in CRM
    # Сначала принудительно заменяем текст "ЛОЖЬ" на 0
    # Пустые строки Pandas при чтении Excel обычно сам превращает в NaN
    calls['Scheduled in CRM'] = calls['Scheduled in CRM'].replace({'ЛОЖЬ': 0, 'False': 0, False: 0})

    # Теперь превращаем в "умный" целочисленный тип, который дружит с пустотами
    calls['Scheduled in CRM'] = calls['Scheduled in CRM'].astype('Int64')

    # 6. Удаление дубликатов
    # Сначала удаляем полные дубликаты, если они есть
    calls = calls.drop_duplicates()
    
    # Теперь ищем скрытые дубликаты: когда ID разные, но суть звонка (время, тип, длительность и т.д.) одинаковая.
    # Создаем список колонок для проверки (все, кроме технических ID)
    ignore_columns = {'Id', 'CONTACTID'}
    subset_columns = [col for col in calls.columns if col not in ignore_columns]
    
    # Удаляем дубликаты по этому подмножеству колонок, оставляя только первое вхождение (keep='first')
    calls = calls.drop_duplicates(subset=subset_columns, keep='first')

    # Считаем строки ПОСЛЕ
    rows_after = len(calls)

    # Сохраняем в CSV
    calls.to_csv('calls_cleaned.csv', index=False)

    print(f"Файл Calls готов. Всего звонков: {len(calls)}")
    
    # Возвращаем данные для отчета
    return {
        'File': 'Calls',
        'Before': rows_before,
        'After': rows_after,
        'Deleted': rows_before - rows_after,
        'Drop %': f"{(rows_before - rows_after) / rows_before:.1%}" if rows_before > 0 else "0%"
    }

if __name__ == "__main__":
    stats = clean_calls()
    print(f"Готово: {stats}")