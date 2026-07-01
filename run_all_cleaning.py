import os
import sys
import time  # Импортируем стандартный модуль для замера времени
import pandas as pd

# Импортируем функции из файлов
from Calls import clean_calls
from Contacts import clean_contacts
from Deals import clean_deals
from Spend import clean_spend

# Настройка путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.append(BASE_DIR)

def run_pipeline():
    print("🚀 Запуск конвейера очистки данных\n")
    
    # Список функций для запуска
    tasks = [
        clean_calls,
        clean_contacts,
        clean_deals,
        clean_spend
    ]
    
    all_stats = []

    for task in tasks:
        # Получаем красивое имя функции (например, "clean_calls")
        task_name = task.__name__
        
        print(f"⌛ Модуль {task_name} запущен в работу...")
        
        # Фиксируем время СТАРТА
        start_time = time.time()
        
        try:
            # Выполняем функцию и получаем статистику
            stats = task()
            
            # Фиксируем время ОКОНЧАНИЯ и считаем разницу
            end_time = time.time()
            execution_time = round(end_time - start_time, 2)
            
            
            # Добавляем при желании время выполнения в словарь статистики
            # stats['Duration (sec)'] = round(execution_time, 2)
            
            all_stats.append(stats)
            
            print(f"✅ {stats['File']} успешно завершен за {execution_time} сек.\n")
            
        except Exception as e:
            print(f"❌ Ошибка в модуле {task.__name__}: {e}")
            break

    # Создаем сводную таблицу
    df_report = pd.DataFrame(all_stats)
    
    print("\n--- СВОДНАЯ ТАБЛИЦА ОЧИСТКИ ---")
    print(df_report.to_string(index=False)) # Вывод таблицы без индексов
    
    # По желанию сохраняем отчет в Excel/CSV
    df_report.to_csv('cleaning_report.csv', index=False)
    print("\n✨ Все данные очищены. Отчет сохранен в 'cleaning_report.csv'")

if __name__ == "__main__":
    run_pipeline()
    input()