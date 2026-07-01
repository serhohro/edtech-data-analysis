import pandas as pd
import os
import sys

# Настройка путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.append(BASE_DIR)

def clean_deals():
    # Загружаем файл, фиксируем ID и Contact Name как строки
    # В ТЗ указано, что Contact Name — это идентификатор контакта по сделке
    deals = pd.read_excel('Deals (Done).xlsx', dtype={'Id': str, 'Contact Name': str})
    
    # Считаем строки ДО
    rows_before = len(deals)

    # 1. Очистка названий колонок
    deals.columns = [col.strip() for col in deals.columns]

    # 2. Преобразование дат в строгий формат datetime (с учетом dayfirst=True)
    deals['Created Time'] = pd.to_datetime(deals['Created_Time' if 'Created_Time' in deals.columns else 'Created Time'], dayfirst=True, errors='coerce')
    deals['Closing Date'] = pd.to_datetime(deals['Closing Date'], dayfirst=True, errors='coerce')

    # 3. Обработка финансовых колонок (Критерий ТЗ №2)
    # В данных бывают значения 0, 1, 9 (демо-доступы) — оставляем их как есть согласно FAQ
    money_cols = ['Initial Amount Paid', 'Offer Total Amount']
    for col in money_cols:
        deals[col] = pd.to_numeric(deals[col], errors='coerce').fillna(0)

    # 4. Обработка Lost Reason
    # В FAQ сказано, что статус Duplicate в Lost Reason означает технический дубль
    # Мы его не удаляем физически, но помечаем или оставляем для фильтрации в BI
    deals['Lost Reason'] = deals['Lost Reason'].fillna('None')
    
    # 5. Заполнение пустых категориальных полей
    deals['Stage'] = deals['Stage'].fillna('Unknown')
    deals['Product'] = deals['Product'].fillna('Not Specified')
    deals['City'] = deals['City'].fillna('Unknown')
    
    # 6. Фильтрация временных аномалий
    # Оставляем только те строки, где дата создания МЕНЬШЕ или РАВНА дате закрытия.
    # Также сохраняем строки, где Closing Date пустая (сделка еще в работе).
    valid_dates_condition = (deals['Created Time'] <= deals['Closing Date']) | (deals['Closing Date'].isna())
    deals = deals[valid_dates_condition]
   
    # 7. Удаление дубликатов
    # Сначала удаляем полные дубликаты, если они есть
    deals = deals.drop_duplicates()
    
    # Ищем скрытые дубликаты (игнорируя технические ID системы)
    ignore_columns = {'Id'} 
    subset_columns = [col for col in deals.columns if col not in ignore_columns]
    
    deals = deals.drop_duplicates(subset=subset_columns, keep='first')
    
    # Считаем строки ПОСЛЕ
    rows_after = len(deals)

    # Сохраняем в CSV
    deals.to_csv('deals_cleaned.csv', index=False)

    print(f"Файл Deals готов. Обработано сделок: {len(deals)}")
    
    # Возвращаем данные для отчета
    return {
        'File': 'Deals',
        'Before': rows_before,
        'After': rows_after,
        'Deleted': rows_before - rows_after,
        'Drop %': f"{(rows_before - rows_after) / rows_before:.1%}" if rows_before > 0 else "0%"
    }

if __name__ == "__main__":
    stats = clean_deals()
    print(f"Готово: {stats}")