import pandas as pd
import os
import sys

# Настройка путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.append(BASE_DIR)

def clean_contacts():
    # Загружаем файл, фиксируем ID как строку
    contacts = pd.read_excel('Contacts (Done).xlsx', dtype={'Id': str})
    
    # Считаем строки ДО
    rows_before = len(contacts)

    # 1. Очистка названий колонок
    contacts.columns = [col.strip() for col in contacts.columns]

    # 2. Преобразование дат
    # Добавляем dayfirst=True, чтобы убрать Warning и корректно читать наши даты
    contacts['Created Time'] = pd.to_datetime(contacts['Created Time'], dayfirst=True, errors='coerce')
    contacts['Modified Time'] = pd.to_datetime(contacts['Modified Time'], dayfirst=True, errors='coerce')

    # 3. Заполнение пустот (согласно ТЗ по обработке отсутствующих значений)
    contacts['Contact Owner Name'] = contacts['Contact Owner Name'].fillna('Unknown')

    # 4. Удаление дубликатов
    # Сначала удаляем полные дубликаты, если они есть
    contacts = contacts.drop_duplicates()
    
    # Теперь ищем скрытые дубликаты: когда ID разные, но суть данных (Contact Owner Name, время) одинаковая.
    # Создаем список колонок для проверки (все, кроме технических ID)
    ignore_columns = {'Id'}
    subset_columns = [col for col in contacts.columns if col not in ignore_columns]
    
    # Удаляем дубликаты по этому подмножеству колонок, оставляя только первое вхождение (keep='first')
    contacts = contacts.drop_duplicates(subset=subset_columns, keep='first')
    
    # Считаем строки ПОСЛЕ
    rows_after = len(contacts)

    # Сохраняем
    contacts.to_csv('contacts_cleaned.csv', index=False)

    print("Файл Contacts готов. ID теперь строка, даты в формате ISO.")
    
    # Возвращаем данные для отчета
    return {
        'File': 'Contacts',
        'Before': rows_before,
        'After': rows_after,
        'Deleted': rows_before - rows_after,
        'Drop %': f"{(rows_before - rows_after) / rows_before:.1%}" if rows_before > 0 else "0%"
    }
    
if __name__ == "__main__":
    stats = clean_contacts()
    print(f"Готово: {stats}")