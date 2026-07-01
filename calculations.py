import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns

from formatter import Formatter

formatter_config = {
    "max_col_width": 50,
    "header_align": "center",
    "header_custom": None,
    "border": True,
    "zebra": True,
    "zebra_colors": ("\033[48;5;235m", "\033[0m"),    # Dark gray background
    "border_chars": {
        "h": "",
        "v": " ",
        "c": ""
    }
}

formatter = Formatter(formatter_config)


# ╔═══════════════════════════════════════════════╗
# ║ ЭТАП 0: Настройка окружения и загрузка данных ║
# ╚═══════════════════════════════════════════════╝

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.append(BASE_DIR)

# Настройка стиля графиков
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.unicode_minus'] = False

print("=== ЗАГРУЗКА И ПРЕДОБРАБОТКА ДАННЫХ ===")

# Загружаем все 4 очищенных датасета
df_deals = pd.read_csv('deals_cleaned.csv')
df_calls = pd.read_csv('calls_cleaned.csv')
df_spend = pd.read_csv('spend_cleaned.csv')
df_contacts = pd.read_csv('contacts_cleaned.csv')

# Принудительное удаление невидимых пробелов в названиях колонок
for name, df in [('Deals', df_deals), ('Calls', df_calls), ('Spend', df_spend), ('Contacts', df_contacts)]:
    before_cols = len(df.columns)
    df.columns = df.columns.str.strip()
    print(f"Таблица {name} успешно загружена. Колонок: {len(df.columns)}")

# Преобразование дат в корректный временной формат для когортного и временного анализа
if 'Created Time' in df_deals.columns:
    df_deals['Created Time'] = pd.to_datetime(df_deals['Created Time'], errors='coerce')
if 'Created Time' in df_contacts.columns:
    df_contacts['Created Time'] = pd.to_datetime(df_contacts['Created Time'], errors='coerce')
if 'Date' in df_spend.columns:
    df_spend['Date'] = pd.to_datetime(df_spend['Date'], errors='coerce')

# Рассчитываем флаг оплаты один раз на всю программу
if 'Stage' in df_deals.columns and 'Initial Amount Paid' in df_deals.columns:
    df_deals['Is_Paid'] = (df_deals['Stage'].str.contains('Paid|Paid Deal|Успешно|Оплачено', case=False, na=False)) | (df_deals['Initial Amount Paid'] > 0)

# ╔════════════════╗
# ║ Поиск аномалий ║
# ╚════════════════╝

# Бизнес-критерии аналитика
MIN_REQUIRED_TIME = 90  # минимальная продолжительность диалога (в секундах)
UPPER_PERCENTILE = df_calls['Call Duration (in seconds)'].quantile(0.99) # получаем 1% длинных звонков

# Общее количество звонков в базе
total_calls = len(df_calls)

# Фильтруем реальную норму
normal_calls = df_calls[
    (df_calls['Call Duration (in seconds)'] >= MIN_REQUIRED_TIME) & 
    (df_calls['Call Duration (in seconds)'] <= UPPER_PERCENTILE)
]

# Считаем аномалии
low_outliers = df_calls[df_calls['Call Duration (in seconds)'] < MIN_REQUIRED_TIME].shape[0]
high_outliers = df_calls[df_calls['Call Duration (in seconds)'] > UPPER_PERCENTILE].shape[0]

# Нормальные звонки (все, что попало МЕЖДУ границами)
normal_calls_df = df_calls[
    (df_calls['Call Duration (in seconds)'] >= MIN_REQUIRED_TIME) & 
    (df_calls['Call Duration (in seconds)'] <= UPPER_PERCENTILE)
]
normal_calls_count = normal_calls_df.shape[0]
normal_calls_average_duration = round(normal_calls['Call Duration (in seconds)'].mean(), 1)

# Расчет процентов
low_pct     = round( (low_outliers / total_calls) * 100, 1 )
high_pct    = round( (high_outliers / total_calls) * 100, 1 )
normal_pct  = round( (normal_calls_count / total_calls) * 100, 1 )

# 1. Готовим данные в виде списка словарей для форматтера
# Каждая запись — это строка таблицы с набором колонок
table_data = [
    {
        "Категория звонков": "Всего звонков в базе данных CRM",
        "Критерий": "–",
        "Количество (шт.)":  total_calls,
        "Доля (%)": 100.0,
        "Ср. длительность": "-"
    },
    {
        "Категория звонков": "Короткие звонки / недозвоны (нижний фильтр)",
        "Критерий": f"< {MIN_REQUIRED_TIME} сек. ({round(MIN_REQUIRED_TIME/60, 1)} мин.)",
        "Количество (шт.)":  low_outliers,
        "Доля (%)": low_pct,
        "Ср. длительность": "-"
    },
    {
        "Категория звонков": "Редкие / сверхдолгие кейсы (верхний фильтр)",
        "Критерий": f"> {round(UPPER_PERCENTILE, 1)} сек. ({round(UPPER_PERCENTILE/60, 1)} мин.)",
        "Количество (шт.)":  high_outliers,
        "Доля (%)": high_pct,
        "Ср. длительность": "-"
    },
    {
        "Категория звонков": "Целевые (нормальные) разговоры",
        "Критерий": f"{round(MIN_REQUIRED_TIME/60, 1)} мин. – {round(UPPER_PERCENTILE/60, 1)} мин.",
        "Количество (шт.)": normal_calls_count,
        "Доля (%)": normal_pct,
        "Ср. длительность": f"{normal_calls_average_duration} сек. ({round(normal_calls_average_duration/60, 1)} мин.)"
    },
]

# 2. Выводим результат в отформатированную таблицу
print("\n=== БИЗНЕС-АНАЛИЗ И СЕГМЕНТАЦИЯ АНОМАЛИЙ В ЗВОНКАХ ===")
print(formatter.make_table(table_data))

# ==========================================
# ЭТАП 0.1: КАЧЕСТВО ДАННЫХ — ЗАПОЛНЕННОСТЬ ВСЕХ ПОЛЕЙ DEALS
# ==========================================
print("\n=== 0.1. АУДИТ КАЧЕСТВА ДАННЫХ: ЗАПОЛНЕННОСТЬ ВСЕХ ПОЛЕЙ ===")

# 1. Автоматически берем ВСЕ колонки
fields_to_check = df_deals.columns.tolist()
raw_quality_data = []
total_records = len(df_deals)

# 2. Собираем сырые данные для последующей сортировки в Pandas
for field in fields_to_check:
    filled_count = df_deals[field].notna().sum()
    fill_rate = (filled_count / total_records) * 100
    raw_quality_data.append({
        "Field": field,
        "Filled": int(filled_count),
        "Missing": int(total_records - filled_count),
        "Rate": fill_rate
    })

# 3. Переводим в DataFrame и сортируем
df_quality = pd.DataFrame(raw_quality_data).sort_values(by='Rate', ascending=True)

# 4. Упаковываем отсортированный DataFrame в формат для твоего форматтера таблиц
data_quality_table = []
for _, row in df_quality.iterrows():
    data_quality_table.append({"Ключевое поле (Deals)": row['Field'], "Заполнено (шт.)": int(row['Filled']), "Пропуски (шт.)": int(row['Missing']), "Степень заполненности (%)": f"{row['Rate']:.2f}"})

print(formatter.make_table(data_quality_table))

# ==========================================
# ЭТАП 0.2: ГЛАВНЫЕ БИЗНЕС-МЕТРИКИ ШКОЛЫ (C-LEVEL DASHBOARD)
# ==========================================
print("\n=== 0.2. СВОДНЫЙ ДАШБОРД КЛЮЧЕВЫХ БИЗНЕС-МЕТРИК ШКОЛЫ ===")
total_revenue = df_deals['Initial Amount Paid'].sum()
total_marketing_spend = df_spend['Spend'].sum() if 'Spend' in df_spend.columns else 0
total_buyers = df_deals[df_deals['Is_Paid'] == True]['Id'].nunique()
total_leads = df_deals['Id'].nunique()

overall_conversion = (total_buyers / total_leads * 100) if total_leads > 0 else 0
overall_romi = ((total_revenue - total_marketing_spend) / total_marketing_spend * 100) if total_marketing_spend > 0 else 0
avg_receipt = df_deals[df_deals['Is_Paid'] == True]['Initial Amount Paid'].mean() if total_buyers > 0 else 0
global_cac = (total_marketing_spend / total_buyers) if total_buyers > 0 else 0

dashboard_data = [
    {"Метрика бизнеса": "Общая фактическая выручка",     "Обозначение": "Revenue",          "Значение": f"{total_revenue:.2f}",            "Размерность": "€"},
    {"Метрика бизнеса": "Общие маркетинговые затраты",   "Обозначение": "Marketing Spend",  "Значение": f"{total_marketing_spend:.2f}",    "Размерность": "€"},
    {"Метрика бизнеса": "Итоговый возврат инвестиций",   "Обозначение": "Overall ROMI",     "Значение": f"{overall_romi:.2f}",              "Размерность": "%"},
    {"Метрика бизнеса": "Всего привлеченных лидов",      "Обозначение": "Leads",            "Значение": f"{total_leads:}",                 "Размерность": "шт."},
    {"Метрика бизнеса": "Всего реальных покупателей",    "Обозначение": "Buyers/Units",     "Значение": f"{total_buyers:}",                "Размерность": "шт."},
    {"Метрика бизнеса": "Сквозная конверсия в оплату",   "Обозначение": "CR",               "Значение": f"{overall_conversion:.2f}",        "Размерность": "%"},
    {"Метрика бизнеса": "Средний чек первого взноса",    "Обозначение": "ARPU",             "Значение": f"{avg_receipt:.2f}",               "Размерность": "€"},
    {"Метрика бизнеса": "Стоимость привлечения клиента", "Обозначение": "Global CAC",       "Значение": f"{global_cac:.2f}",                "Размерность": "€"}
]
print(formatter.make_table(dashboard_data))

# ==========================================
# ЭТАП 1: Расчет описательной статистики
# ==========================================
def get_numerical_stats(df, columns, table_name):
    valid_cols = [c for c in columns if c in df.columns]
    if not valid_cols:
        return pd.DataFrame()

    temp = df[valid_cols].copy()
    
    # Внутренняя очистка строк от мусорных символов валют перед расчетом метрик
    for col in valid_cols:
        if temp[col].dtype == 'object':
            temp[col] = temp[col].astype(str).str.replace(r'[^\d.,]', '', regex=True).str.replace(',', '.')
        temp[col] = pd.to_numeric(temp[col], errors='coerce')

    res = temp.describe().T
    res['median'] = temp.median()
    mode_val = temp.mode()
    res['mode'] = mode_val.iloc[0] if not mode_val.empty else np.nan
    res['range'] = res['max'] - res['min']
    res['table'] = table_name
    
    return res[['table', 'mean', 'median', 'mode', 'range', 'std']]

# Списки ИСТИННО числовых параметров (без категориальных длительностей курсов!)
deals_cols = ['Initial Amount Paid', 'Offer Total Amount']  # Убрали Course duration и Months of study
spend_cols = ['Impressions', 'Clicks', 'Spend']

# ДЛЯ ЗВОНКОВ ПЕРЕДАЕМ ОЧИЩЕННЫЙ ДАТАФРЕЙМ (Решаем проблему аномалий!)
calls_cols = ['Call Duration (in seconds)']

stats_list = []
stats_list.append(get_numerical_stats(df_deals, deals_cols, 'Deals'))
# Передаем normal_calls_df, чтобы статистика считалась только по нормальным разговорам!
stats_list.append(get_numerical_stats(normal_calls_df, calls_cols, 'Calls')) 
stats_list.append(get_numerical_stats(df_spend, spend_cols, 'Spend'))
full_stats = pd.concat(stats_list)

# Подготавливаем DataFrame для форматтера
formatter_df = full_stats.reset_index().rename(columns={'index': 'Показатель (Поле)'}).round(2)
numerical_stats_data = formatter_df.to_dict(orient='records')

print("\n=== 1. ОПИСАТЕЛЬНАЯ СТАТИСТИКА ЧИСЛОВЫХ ПОЛЕЙ (БЕЗ АНОМАЛИЙ И КАТЕГОРИЙ) ===")
print(formatter.make_table(numerical_stats_data))

# ==========================================
# ЭТАП 2: Анализ контактов и эффективности менеджеров
# ==========================================
print("\n=== 2. АНАЛИЗ ДАТАСЕТА КОНТАКТОВ И ЭФФЕКТИВНОСТИ МЕНЕДЖЕРОВ ===")

if 'Contact Owner Name' in df_contacts.columns:
    # 1. Считаем абсолютное количество контактов на каждого менеджера
    contacts_counts = df_contacts['Contact Owner Name'].value_counts(dropna=False)
    total_contacts = len(df_contacts)
    
    # Имя колонки в сделках для связи
    deal_manager_col = 'Deal Owner Name' if 'Deal Owner Name' in df_deals.columns else 'Created By'
    
    if deal_manager_col in df_deals.columns:
        manager_finance = df_deals.groupby(deal_manager_col).agg(
            Revenue=('Initial Amount Paid', 'sum'),
            Sales_Count=('Is_Paid', 'sum')
        ).to_dict('index')
    else:
        manager_finance = {}

    # Сначала считаем глобальную выручку по всем, чтобы правильно вычислить доли менеджеров
    total_revenue_all = sum(f.get('Revenue', 0.0) for f in manager_finance.values())
    total_sales_all = 0
    
    # 2. Собираем СЫРЫЕ данные в список для промежуточного DataFrame
    raw_manager_list = []
    
    for owner, count in contacts_counts.items():
        owner_name = "Не определено" if str(owner) in ['False', 'nan', 'None', ''] else str(owner)
        share_pct = (count / total_contacts) * 100
        
        fin_data = manager_finance.get(owner, {'Revenue': 0.0, 'Sales_Count': 0})
        rev = fin_data['Revenue']
        sales = fin_data['Sales_Count']
        
        total_sales_all += sales
        
        # Считаем конверсию менеджера (Продажи / Контакты)
        conversion_rate = (sales / count * 100) if count > 0 else 0.0
        
        # Считаем долю от общей выручки всей школы
        rev_share_pct = (rev / total_revenue_all * 100) if total_revenue_all > 0 else 0.0
        
        # Считаем разницу эффективности (Доля выручки - Доля базы)
        efficiency_delta = rev_share_pct - share_pct
        
        raw_manager_list.append({
            "Manager_Key": owner, "Менеджер": owner_name, "Контакты (шт.)": count, "Продажи (шт.)": int(sales),
            "Конверсия": conversion_rate, "Доля базы": share_pct, "Выручка_Доля": rev_share_pct, 
            "Эффективность": efficiency_delta, "Revenue_Raw": rev
        })
        
    # 3. Переводим в DataFrame и СОРТИРУЕМ ПО ВЫРУЧКЕ (по убыванию)
    df_managers_sorted = pd.DataFrame(raw_manager_list).sort_values(by='Revenue_Raw', ascending=False)
    
    # 4. Формируем финальный список для форматтера с идеальным порядком столбцов
    contacts_data = []
    for _, row in df_managers_sorted.iterrows():
        avg_check = (row['Revenue_Raw'] / row['Продажи (шт.)']) if row['Продажи (шт.)'] > 0 else 0.0
        
        # Добавляем красивый плюс перед положительной эффективностью для наглядности
        eff_val = row['Эффективность']
        eff_str = f"+{eff_val:.2f}" if eff_val > 0 else f"{eff_val:.2f}"
        
        contacts_data.append({
            "Менеджер": row['Менеджер'],
            "Контакты (шт.)": int(row['Контакты (шт.)']),
            "Продажи (шт.)": int(row['Продажи (шт.)']),
            "Конверсия, %": f"{row['Конверсия']:.2f}",
            "Доля базы, %": f"{row['Доля базы']:.2f}",
            "Выручка, %": f"{row['Выручка_Доля']:.2f}",
            "Выручка, €": f"{row['Revenue_Raw']:.2f}",
            "Средний чек, €": f"{avg_check:.2f}"
        })
        
    # Считаем глобальные показатели по школе для строки ИТОГО
    global_conversion = (total_sales_all / total_contacts * 100) if total_contacts > 0 else 0.0
    global_avg_check = (total_revenue_all / total_sales_all) if total_sales_all > 0 else 0.0
    
    # Добавляем финальную строку ИТОГО
    contacts_data.append({
        "Менеджер": "ИТОГО по школе",
        "Контакты (шт.)": total_contacts,
        "Продажи (шт.)": int(total_sales_all),
        "Конверсия, %": f"{global_conversion:.2f}",
        "Доля базы, %": "100.00",
        "Выручка, %": "100.00",
        "Выручка, €": f"{total_revenue_all:.2f}",
        "Средний чек, €": f"{global_avg_check:.2f}"
    })
    
    # 5. Выводим результат через форматтер
    print(formatter.make_table(contacts_data))
else:
    print("Ошибка: Колонка 'Contact Owner Name' не найдена в датасете контактов.")

# ==========================================
# ЭТАП 3: Категориальный анализ и Конверсии
# ==========================================

print("\n=== 3. АНАЛИЗ УРОВНЕЙ ЯЗЫКА ПО VALUE SCORE (ОБЪЕМ × КОНВЕРСИЯ) ===")

# 1. Функция нормализации уровней
def normalize_german_level(level):
    if pd.isna(level):
        return "Не определено"
    level = str(level).strip().upper()
    mapping = {
        'А1': 'A1', 'A1': 'A1',
        'А2': 'A2', 'A2': 'A2',
        'В1': 'B1', 'Б1': 'B1', 'B1': 'B1',
        'В2': 'B2', 'B2': 'B2',
        'С1': 'C1', 'C1': 'C1',
        'С2': 'C2', 'C2': 'C2'
    }
    return mapping.get(level, "Не определено")

if 'Level of Deutsch' in df_deals.columns:
    # Очистка уровней и определение факта оплаты
    df_deals['Level_Clean'] = df_deals['Level of Deutsch'].apply(normalize_german_level)
    df_deals['Is_Paid'] = (df_deals['Stage'].str.contains('Paid|Paid Deal|Успешно|Оплачено', case=False, na=False)) | (df_deals['Initial Amount Paid'] > 0)

    # Базовая агрегация (Воронка)
    level_analysis = df_deals.groupby('Level_Clean').agg(
        Total_Deals=('Id', 'count'),
        Paid_Deals=('Is_Paid', 'sum')
    ).reset_index()

    # Расчет базовой конверсии
    level_analysis['Conversion_%'] = (level_analysis['Paid_Deals'] / level_analysis['Total_Deals'] * 100).round(2)

    # Расчет доли рынка и Value Score
    total_all_deals = level_analysis['Total_Deals'].sum()
    paid_all_deals = level_analysis['Paid_Deals'].sum()
    level_analysis['Lead_Share_%'] = ((level_analysis['Total_Deals'] / total_all_deals) * 100).round(2)
    # Формула комплексной ценности: Доля рынка * Конверсия / 10
    level_analysis['Value_Score'] = ((level_analysis['Lead_Share_%'] * level_analysis['Conversion_%']) / 10).round(2)

    # --- ЛОГИКА СОРТИРОВКИ С ПЕРЕНОСОМ «НЕ ОПРЕДЕЛЕНО» ВКОНЕЦ ---
    df_recognized = level_analysis[level_analysis['Level_Clean'] != "Не определено"].copy()
    df_unrecognized = level_analysis[level_analysis['Level_Clean'] == "Не определено"].copy()

    # Сортируем распознанные уровни по Value Score от большего к меньшему
    df_recognized = df_recognized.sort_values(by='Value_Score', ascending=False)

    # Склеиваем обратно
    final_level_analysis = pd.concat([df_recognized, df_unrecognized], ignore_index=True)

    # --- ПОДГОТОВКА ДАННЫХ ДЛЯ ФОРМАТТЕРАТАБЛИЦ ---
    levels_table_data = []
    
    # Итерируемся по строкам и собираем красивый List[Dict]
    for _, row in final_level_analysis.iterrows():
        levels_table_data.append({
            "Уровень немецкого": row['Level_Clean'],
            "Всего сделок (шт.)": int(row['Total_Deals']),
            "Оплаты (шт.)": int(row['Paid_Deals']),
            "Конверсия (%)": f"{row['Conversion_%']:.2f}",
            "Доля рынка (%)": f"{row['Lead_Share_%']:.2f}",
            "Value Score": f"{row['Value_Score']:.2f}"
        })
        
    # Считаем общую конверсию по всей школе для строки ИТОГО
    total_conversion = (paid_all_deals / total_all_deals * 100) if total_all_deals > 0 else 0
    
    # Добавляем строку ИТОГО в самый конец таблицы
    levels_table_data.append({
        "Уровень немецкого": "ИТОГО / Ср. по школе",
        "Всего сделок (шт.)": int(total_all_deals),
        "Оплаты (шт.)": int(paid_all_deals),
        "Конверсия (%)": f"{total_conversion:.2f}",
        "Доля рынка (%)": "100.00",
        "Value Score": "-"
    })
    
    # Выводим готовую форматированную таблицу
    print(formatter.make_table(levels_table_data))
else:
    print("Ошибка: Колонка 'Level of Deutsch' не найдена в датасете сделок.")


print("\n=== 3.1. КАТЕГОРИАЛЬНЫЙ АНАЛИЗ ДЛИТЕЛЬНОСТИ КУРСОВ И КОНВЕРСИИ ===")

for col_name, label in [('Course duration', 'Длительность курса (мес.)'), ('Months of study', 'Срок обучения (мес.)')]:
    if col_name in df_deals.columns:
        
        # 1. Считаем агрегацию, сохраняя пропуски как NaN, чтобы не ломать типы данных для сортировки
        cat_analysis = df_deals.groupby(col_name, dropna=False).agg(
            Total_Deals=('Id', 'count'),
            Paid_Deals=('Is_Paid', 'sum')
        ).reset_index()
        
        # Считаем конверсию
        cat_analysis['Conversion_%'] = (cat_analysis['Paid_Deals'] / cat_analysis['Total_Deals'] * 100).round(2)
        
        # 2. РАЗДЕЛЯЕМ ДЛЯ ПРАВИЛЬНОЙ СОРТИРОВКИ
        # Выделяем строки с числовыми значениями (исключаем NaN)
        df_num = cat_analysis[cat_analysis[col_name].notna()].copy()
        # Принудительно приводим к числовому типу, чтобы 10 месяцев не встали после 1 месяца
        df_num[col_name] = pd.to_numeric(df_num[col_name])
        df_num = df_num.sort_values(by=col_name)
        
        # Выделяем строку с пропусками
        df_none = cat_analysis[cat_analysis[col_name].isna()].copy()
        
        # 3. СКЛЕИВАЕМ И ПЕРЕВОДИМ В СТРОКИ
        final_cat = pd.concat([df_num, df_none], ignore_index=True)
        
        # --- ПОДГОТОВКА ДАННЫХ ДЛЯ ФОРМАТТЕРА ТАБЛИЦ ---
        cat_table_data = []
        for _, row in final_cat.iterrows():
            # Если значение было NaN, превращаем его в красивый текст
            if pd.isna(row[col_name]):
                val_display = "Не указано"
            else:
                # Превращаем в int, чтобы убрать некрасивые хвосты .0 (например, "3.0" -> "3")
                val_display = str(int(row[col_name]))
                
            cat_table_data.append({
                label: val_display,
                "Всего сделок (шт.)": int(row['Total_Deals']),
                "Оплаты (шт.)": int(row['Paid_Deals']),
                "Конверсия (%)": f"{row['Conversion_%']:.2f}"
            })
            
        print(f"\nРаспределение по полю: {col_name}")
        print(formatter.make_table(cat_table_data))


print("\n=== 3.2. АНАЛИЗ ВОРОНКИ, КАЧЕСТВА ЛИДОВ И ПРИЧИН ОТКАЗОВ ===")

# 1. Анализ этапов сделок (Stage)
if 'Stage' in df_deals.columns:
    stage_analysis = df_deals.groupby('Stage', dropna=False).agg(
        Total_Deals=('Id', 'count'),
        Paid_Deals=('Is_Paid', 'sum')
    ).reset_index()
    
    stage_analysis['Conversion_%'] = (stage_analysis['Paid_Deals'] / stage_analysis['Total_Deals'] * 100).round(2)
    stage_analysis = stage_analysis.sort_values(by='Total_Deals', ascending=False)
    
    stage_table_data = []
    for _, row in stage_analysis.iterrows():
        stage_table_data.append({
            "Этап сделки (Stage)": "Не указан" if pd.isna(row['Stage']) else str(row['Stage']),
            "Количество (шт.)": int(row['Total_Deals']),
            "Оплаты (шт.)": int(row['Paid_Deals']),
            "Конверсия в оплату": f"{row['Conversion_%']:.2f}"
        })
    print("\nРаспределение сделок по этапам воронки:")
    print(formatter.make_table(stage_table_data))

# 2. Анализ качества лидов (Quality)
if 'Quality' in df_deals.columns:
    quality_analysis = df_deals.groupby('Quality', dropna=False).agg(
        Total_Deals=('Id', 'count'),
        Paid_Deals=('Is_Paid', 'sum')
    ).reset_index()
    
    quality_analysis['Conversion_%'] = (quality_analysis['Paid_Deals'] / quality_analysis['Total_Deals'] * 100).round(2)
    quality_analysis = quality_analysis.sort_values(by='Total_Deals', ascending=False)
    
    quality_table_data = []
    for _, row in quality_analysis.iterrows():
        quality_table_data.append({
            "Качество лида (Quality)": "Не указано" if pd.isna(row['Quality']) else str(row['Quality']),
            "Количество (шт.)": int(row['Total_Deals']),
            "Оплаты (шт.)": int(row['Paid_Deals']),
            "Конверсия в оплату": f"{row['Conversion_%']:.2f}"
        })
    print("\nАнализ конверсии в зависимости от качества лида:")
    print(formatter.make_table(quality_table_data))

# 3. Анализ причин отказов (Lost Reason) — берем только проигранные сделки
if 'Lost Reason' in df_deals.columns:
    # Фильтруем сделки, где есть причина отказа, либо этап содержит закрыто/проиграно
    lost_deals = df_deals[df_deals['Lost Reason'].notna() | df_deals['Stage'].str.contains('Lost|Проиграно|Отказ', case=False, na=False)].copy()
    
    if not lost_deals.empty:
        lost_analysis = lost_deals.groupby('Lost Reason', dropna=False).size().reset_index(name='Count')
        total_lost = lost_analysis['Count'].sum()
        lost_analysis['Share_%'] = (lost_analysis['Count'] / total_lost * 100).round(2)
        lost_analysis = lost_analysis.sort_values(by='Count', ascending=False)
        
        lost_table_data = []
        for _, row in lost_analysis.iterrows():
            lost_table_data.append({
                "Причина отказа (Lost Reason)": "Причина не детализирована" if pd.isna(row['Lost Reason']) else str(row['Lost Reason']),
                "Количество отказов (шт.)": int(row['Count']),
                "Доля от всех отказов (%)": f"{row['Share_%']:.2f}"
            })
        print("\nТОП причин проигрыша сделок (структура упущенных возможностей):")
        print(formatter.make_table(lost_table_data))

# 1. Сквозная конверсионная воронка (от UA лидов / контактов)
print("\nРаспределение сделок по классической кумулятивной воронке продаж:")
# Считаем шаги
step_contacts = len(df_contacts) # Всего зашло в CRM
step_deals = df_deals['Id'].nunique() # Дошли до этапа сделки
step_paid = df_deals[df_deals['Is_Paid'] == True]['Id'].nunique() # Оплатили

funnel_table_data = [
    {
        "Этап воронки": "1. Зарегистрировано контактов (UA Лиды)",
        "Объем (юниты)": int(step_contacts),
        "Конверсия к первому шагу (%)": "100.00",
        "Конверсия к предыдущему шагу (%)": "100.00"
    },
    {
        "Этап воронки": "2. Сформировано сделок в CRM",
        "Объем (юниты)": int(step_deals),
        "Конверсия к первому шагу (%)": f"{(step_deals/step_contacts*100):.2f}",
        "Конверсия к предыдущему шагу (%)": f"{(step_deals/step_contacts*100):.2f}"
    },
    {
        "Этап воронки": "3. Успешные оплаты (Покупатели)",
        "Объем (юниты)": int(step_paid),
        "Конверсия к первому шагу (%)": f"{(step_paid/step_contacts*100):.2f}",
        "Конверсия к предыдущему шагу (%)": f"{(step_paid/step_deals*100):.2f}" if step_deals > 0 else "0.00"
    }
]
print(formatter.make_table(funnel_table_data))

# ==========================================
# ЭТАП 4: Маркетинговые метрики и расчет ROMI
# ==========================================
print("\n=== 4. МАРКЕТИНГОВЫЕ МЕТРИКИ (ROMI) И ЭФФЕКТИВНОСТЬ КАНАЛОВ ===")

if 'Source' in df_deals.columns and 'Source' in df_spend.columns:
    # 1. Группируем доходы и расходы
    rev_by_source = df_deals.groupby('Source')['Initial Amount Paid'].sum()
    spend_by_source = df_spend.groupby('Source')['Spend'].sum()
    
    # 2. Объединяем таблицы
    romi_df = pd.DataFrame({'Revenue': rev_by_source, 'Spend': spend_by_source}).fillna(0)
    
    # 3. Считаем чистый ROMI (в числах)
    romi_df['ROMI_%'] = ((romi_df['Revenue'] - romi_df['Spend']) / romi_df['Spend'] * 100)
    romi_df['ROMI_%'] = romi_df['ROMI_%'].replace([np.inf, -np.inf], np.nan)
    
    # 4. Сортируем по ROMI от большего к меньшему, пока NaN на месте
    romi_df = romi_df.sort_values(by='ROMI_%', ascending=False)
    
    # --- ПОДГОТОВКА ДАННЫХ ДЛЯ ФОРМАТТЕРА ТАБЛИЦ ---
    romi_table_data = []
    
    # Итерируемся по строкам датафрейма
    for source, row in romi_df.iterrows():
        # Обрабатываем отображение процентов ROMI
        romi_display = "—" if pd.isna(row['ROMI_%']) else f"{row['ROMI_%']:.2f}"
        
        romi_table_data.append({
            "Источник трафика": source,
            "Выручка (Revenue)": f"{row['Revenue']:.2f}",
            "Затраты (Spend)": f"{row['Spend']:.2f}",
            "Показатель ROMI (%)": romi_display
        })
    
    # 5. Считаем глобальные итоги для строки ИТОГО
    total_revenue = romi_df['Revenue'].sum()
    total_spend = romi_df['Spend'].sum()
    
    if total_spend > 0:
        total_romi = ((total_revenue - total_spend) / total_spend) * 100
        total_romi_display = f"{total_romi:.2f}"
    else:
        total_romi_display = "—"
        
    # Добавляем финальную строку итогов в самый конец таблицы
    romi_table_data.append({
        "Источник трафика": "ИТОГО по маркетингу",
        "Выручка (Revenue)": f"{total_revenue:.2f}",
        "Затраты (Spend)": f"{total_spend:.2f}",
        "Показатель ROMI (%)": total_romi_display
    })
    
    # 6. Выводим результат через форматтер
    print(formatter.make_table(romi_table_data))
else:
    print("Ошибка: Колонка 'Source' не найдена в датасетах сделок или расходов.")

# ╔════════════════════════════════════════════════════╗
# ║ ЭТАП 5: Географический анализ и региональные рынки ║
# ╚════════════════════════════════════════════════════╝

print("\n=== 5. ГЕОГРАФИЧЕСКИЙ АНАЛИЗ И РЕГИОНАЛЬНЫЕ РЫНКИ ===")

if 'City' in df_deals.columns:
    # 1. Базовая предобработка названий городов
    df_deals['City_Clean'] = df_deals['City'].fillna('Unknown').astype(str).str.strip()
    df_deals['City_Clean'] = df_deals['City_Clean'].replace(['-', '—', 'none', 'None'], 'Unknown')
    
    # Проверяем расчет флага оплаты
    df_deals['Is_Paid'] = (df_deals['Stage'].str.contains('Paid|Paid Deal|Успешно|Оплачено', case=False, na=False)) | (df_deals['Initial Amount Paid'] > 0)
    
    # 2. Первичная агрегация по всем уникальным значениям
    geo_raw = df_deals.groupby('City_Clean').agg(
        Total_Deals=('Id', 'count'),
        Paid_Deals=('Is_Paid', 'sum'),
        Revenue=('Initial Amount Paid', 'sum')
    ).reset_index()
    
    # Расчет базовой конверсии
    geo_raw['Conversion_%'] = (geo_raw['Paid_Deals'] / geo_raw['Total_Deals'] * 100).round(2)
    
    # 3. Изолируем категорию Unknown
    df_unknown = geo_raw[geo_raw['City_Clean'].str.lower() == 'unknown'].copy()
    df_cities_only = geo_raw[geo_raw['City_Clean'].str.lower() != 'unknown'].copy()
    
    # 4. Выделяем ТОП-15 реальных городов по объему выручки
    top_15 = df_cities_only.sort_values(by='Revenue', ascending=False).head(15).copy()
    
    # 5. Все остальные города схлопываем в группу "Другие города"
    other_cities_mask = ~df_cities_only['City_Clean'].isin(top_15['City_Clean'])
    df_others = df_cities_only[other_cities_mask]
    
    if not df_others.empty:
        others_row = pd.DataFrame([{
            'City_Clean': 'Другие города',
            'Total_Deals': df_others['Total_Deals'].sum(),
            'Paid_Deals': df_others['Paid_Deals'].sum(),
            'Revenue': df_others['Revenue'].sum(),
            'Conversion_%': (df_others['Paid_Deals'].sum() / df_others['Total_Deals'].sum() * 100).round(2)
        }])
    else:
        others_row = pd.DataFrame(columns=geo_raw.columns)
        
    # Форматируем отображение Unknown для финального отчета
    if not df_unknown.empty:
        df_unknown['City_Clean'] = 'Unknown / Регион не указан'
        df_unknown['Conversion_%'] = (df_unknown['Paid_Deals'].sum() / df_unknown['Total_Deals'].sum() * 100).round(2)
        
    # 6. Склеиваем в строго заданном порядке: ТОП-15 -> Другие города -> Unknown
    final_geo_report = pd.concat([top_15, others_row, df_unknown], ignore_index=True)
    
    # --- ПОДГОТОВКА ДАННЫХ ДЛЯ ФОРМАТТЕРА ТАБЛИЦ ---
    geo_table_data = []
    
    # Итерируемся по собранному отчету
    for _, row in final_geo_report.iterrows():
        geo_table_data.append({
            "Город": row['City_Clean'],
            "Всего сделок (шт.)": int(row['Total_Deals']),
            "Оплаты (шт.)": int(row['Paid_Deals']),
            "Конверсия (%)": f"{row['Conversion_%']:.2f}",
            "Выручка (€)": f"{row['Revenue']:.0f}"
        })
        
    # Считаем глобальные итоги для финальной строки таблицы
    total_geo_deals = geo_raw['Total_Deals'].sum()
    total_geo_paid = geo_raw['Paid_Deals'].sum()
    total_geo_revenue = geo_raw['Revenue'].sum()
    avg_geo_conversion = (total_geo_paid / total_geo_deals * 100) if total_geo_deals > 0 else 0
    
    # Добавляем строку ИТОГО
    geo_table_data.append({
        "Город": "ИТОГО по всей географии",
        "Всего сделок (шт.)": int(total_geo_deals),
        "Оплаты (шт.)": int(total_geo_paid),
        "Конверсия (%)": f"{avg_geo_conversion:.2f}",
        "Выручка (€)": f"{total_geo_revenue:.0f}"
    })
    
    # Выводим результат через форматтер
    print(formatter.make_table(geo_table_data))
else:
    print("Ошибка: Колонка 'City' не найдена в датасете сделок.")

# ╔════════════════════════════════════════════╗
# ║ ЭТАП 6: Юнит-экономика в разрезе продуктов ║
# ╚════════════════════════════════════════════╝

print("\n=== 6. ЮНИТ-ЭКОНОМИКА В РАЗРЕЗЕ ПРОДУКТОВ ===")

if 'Product' in df_deals.columns:
    # 1. Очистка названий продуктов
    df_deals['Product_Clean'] = df_deals['Product'].fillna('Не указан').astype(str).str.strip()
    
    # 2. Фильтруем только успешные (оплаченные) сделки
    df_deals['Is_Paid'] = (df_deals['Stage'].str.contains('Paid|Paid Deal|Успешно|Оплачено', case=False, na=False)) | (df_deals['Initial Amount Paid'] > 0)
    paid_deals_only = df_deals[df_deals['Is_Paid'] == True].copy()
    
    # 3. Считаем агрегированные показатели по каждому продукту (без длительности курса!)
    product_economy = paid_deals_only.groupby('Product_Clean').agg(
        Buyers=('Id', 'count'),                       # Количество покупателей
        Total_Revenue=('Initial Amount Paid', 'sum'), # Общий фактический доход
        Avg_Initial_Paid=('Initial Amount Paid', 'mean'), # Сколько в среднем платят за раз
        Avg_Offer_Price=('Offer Total Amount', 'mean')   # Полная средняя цена контракта
    ).reset_index()
    
    # 4. Расчет маркетинговых затрат (Spend) и базового CAC
    total_marketing_spend = df_spend['Spend'].sum() if 'Spend' in df_spend.columns else 0
    total_paid_deals = product_economy['Buyers'].sum()
    
    # Средний CAC по школе
    base_cac = (total_marketing_spend / total_paid_deals) if total_paid_deals > 0 else 0
    
    # Добавляем CAC и маржинальность юнита
    product_economy['Unit_CAC'] = base_cac
    product_economy['Unit_Margin'] = product_economy['Avg_Initial_Paid'] - product_economy['Unit_CAC']
    
    # Сортируем по популярности (количеству покупателей)
    product_economy = product_economy.sort_values(by='Buyers', ascending=False)
    
    # --- ПОДГОТОВКА ДАННЫХ ДЛЯ ФОРМАТТЕРА ТАБЛИЦ ---
    product_table_data = []
    
    for _, row in product_economy.iterrows():
        product_table_data.append({
            "Продукт": row['Product_Clean'],
            "Покупатели": int(row['Buyers']),
            "Полный чек": f"{row['Avg_Offer_Price']:.2f}",
            "Первый взнос": f"{row['Avg_Initial_Paid']:.2f}",
            "Стоимость привлечения": f"{row['Unit_CAC']:.2f}",
            "Юнит-маржа": f"{row['Unit_Margin']:.2f}",
            "Общая выручка": f"{row['Total_Revenue']:.0f}"
        })
        
    # 5. Считаем глобальные средние показатели для строки ИТОГО
    global_avg_offer = paid_deals_only['Offer Total Amount'].mean() if total_paid_deals > 0 else 0
    global_avg_initial = paid_deals_only['Initial Amount Paid'].mean() if total_paid_deals > 0 else 0
    global_margin = global_avg_initial - base_cac  # <--- ТУТ ИСПРАВЛЕНО (переменная указана верно)
    global_total_revenue = paid_deals_only['Initial Amount Paid'].sum()
    
    # Добавляем финальную строку итогов
    product_table_data.append({
        "Продукт": "ИТОГО / Среднее по школе",
        "Покупатели": int(total_paid_deals),
        "Полный чек": f"{global_avg_offer:.2f}",
        "Первый взнос": f"{global_avg_initial:.2f}",
        "Стоимость привлечения": f"{base_cac:.2f}",
        "Юнит-маржа": f"{global_margin:.2f}",
        "Общая выручка": f"{global_total_revenue:.0f}"
    })
    
    # 6. Выводим результат через твой форматтер
    print(formatter.make_table(product_table_data))
else:
    print("Ошибка: Колонка 'Product' не найдена в датасете сделок.")


# ==========================================
# ЭТАП 7: ВИЗУАЛИЗАЦИИ (ГРАФИКИ)
# ==========================================
print("\n=== 7. ВИЗУАЛИЗАЦИИ И ГРАФИКИ ===")

# 1. Динамика создания сделок по месяцам
if 'Created Time' in df_deals.columns and len(df_deals) > 0:
    deals_over_time = df_deals.resample('ME', on='Created Time').size()
    if len(deals_over_time) > 0:
        plt.figure(figsize=(12, 6))
        deals_over_time.plot(kind='line', marker='o', color='#2ecc71', linewidth=2, markersize=8)
        plt.title('Динамика создания сделок по месяцам', fontsize=15, fontweight='bold')
        plt.xlabel('Дата', fontsize=12)
        plt.ylabel('Количество сделок', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        for i, (date, value) in enumerate(deals_over_time.items()):
            plt.annotate(str(value), (date, value), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9)
        plt.tight_layout()
        plt.show()
        print("✓ График 1: Динамика сделок")

# 2. Конверсия по уровням немецкого языка
if 'final_level_analysis' in locals() and len(final_level_analysis) > 0:
    levels_plot = final_level_analysis[final_level_analysis['Level_Clean'] != "Не определено"].copy()
    if len(levels_plot) > 0:
        plt.figure(figsize=(10, 6))
        bars = plt.bar(levels_plot['Level_Clean'], levels_plot['Conversion_%'], color='teal', alpha=0.7)
        plt.title('Конверсия в оплату в зависимости от уровня языка', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45)
        plt.ylabel('Конверсия (%)', fontsize=12)
        plt.xlabel('Уровень немецкого', fontsize=12)
        for bar, val in zip(bars, levels_plot['Conversion_%']):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{val:.1f}%', ha='center', fontsize=10, fontweight='bold')
        plt.tight_layout()
        plt.show()
        print("✓ График 2: Конверсия по уровням языка")

# 3. Топ-10 продуктов по выручке
if 'Product' in df_deals.columns:
    product_revenue = df_deals.groupby('Product')['Initial Amount Paid'].sum().sort_values(ascending=False).head(10)
    if len(product_revenue) > 0 and product_revenue.sum() > 0:
        plt.figure(figsize=(10, 6))
        colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(product_revenue)))
        bars = plt.barh(product_revenue.index, product_revenue.values, color=colors)
        plt.title('Топ-10 продуктов по выручке', fontsize=14, fontweight='bold')
        plt.xlabel('Сумма (евро)', fontsize=12)
        plt.gca().invert_yaxis()
        for bar in bars:
            plt.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2, 
                    f'€{bar.get_width():,.0f}', va='center', fontsize=9)
        plt.tight_layout()
        plt.show()
        print("✓ График 3: Топ продуктов по выручке")

# 4. ROMI по рекламным каналам
if 'Source' in df_deals.columns and 'Source' in df_spend.columns:
    romi_plot_data = romi_df.dropna().head(10).reset_index()
    if len(romi_plot_data) > 0:
        plt.figure(figsize=(12, 6))
        colors = ['green' if x > 0 else 'red' for x in romi_plot_data['ROMI_%']]
        bars = plt.barh(romi_plot_data['Source'], romi_plot_data['ROMI_%'], color=colors, alpha=0.7)
        plt.title('ROMI по рекламным каналам (%)', fontsize=14, fontweight='bold')
        plt.xlabel('ROMI (%)', fontsize=12)
        plt.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
        for bar in bars:
            width = bar.get_width()
            offset = 5 if width > 0 else -40
            plt.text(width + offset, bar.get_y() + bar.get_height()/2, 
                    f'{width:.0f}%', va='center', fontsize=9)
        plt.tight_layout()
        plt.show()
        print("✓ График 4: ROMI по каналам")

# 5. Топ-10 городов по количеству лидов
if 'City' in df_deals.columns and 'final_geo_report' in locals() and len(final_geo_report) > 0:
    cities_for_plot = final_geo_report[
        (final_geo_report['City_Clean'] != 'Unknown') & 
        (final_geo_report['City_Clean'] != 'Другие города')
    ].head(10).copy()
    
    if len(cities_for_plot) > 0:
        plt.figure(figsize=(12, 6))
        colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(cities_for_plot)))
        bars = plt.barh(cities_for_plot['City_Clean'], cities_for_plot['Total_Deals'], color=colors)
        plt.title('Топ-10 городов по количеству лидов', fontsize=14, fontweight='bold')
        plt.xlabel('Количество лидов', fontsize=12)
        plt.gca().invert_yaxis()
        for bar in bars:
            plt.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, 
                    f'{int(bar.get_width())}', va='center', fontsize=10, fontweight='bold')
        plt.tight_layout()
        plt.show()
        print("✓ График 5: Топ городов по лидам")

# 6. Топ-10 городов по выручке
if 'City' in df_deals.columns and 'final_geo_report' in locals() and len(final_geo_report) > 0:
    revenue_cities = final_geo_report[
        (final_geo_report['City_Clean'] != 'Unknown') & 
        (final_geo_report['City_Clean'] != 'Другие города')
    ].head(10).copy()
    
    if len(revenue_cities) > 0 and revenue_cities['Revenue'].sum() > 0:
        plt.figure(figsize=(12, 6))
        colors = plt.cm.Reds(np.linspace(0.4, 0.9, len(revenue_cities)))
        bars = plt.barh(revenue_cities['City_Clean'], revenue_cities['Revenue'], color=colors)
        plt.title('Топ-10 городов по выручке (евро)', fontsize=14, fontweight='bold')
        plt.xlabel('Выручка (евро)', fontsize=12)
        plt.gca().invert_yaxis()
        for bar in bars:
            plt.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2, 
                    f'€{bar.get_width():,.0f}', va='center', fontsize=9)
        plt.tight_layout()
        plt.show()
        print("✓ График 6: Топ городов по выручке")

# 7. Эффективность менеджеров (конверсия)
if 'Deal Owner Name' in df_deals.columns:
    sales_performance = df_deals.groupby('Deal Owner Name').agg(
        Total_Deals=('Id', 'count'),
        Paid_Deals=('Is_Paid', 'sum'),
        Total_Revenue=('Initial Amount Paid', 'sum')
    ).reset_index()
    sales_performance['Conversion_%'] = (sales_performance['Paid_Deals'] / sales_performance['Total_Deals'] * 100).round(2)
    sales_performance = sales_performance.sort_values(by='Conversion_%', ascending=False)
    top_managers = sales_performance.head(10)
    
    if len(top_managers) > 0:
        plt.figure(figsize=(12, 6))
        colors = plt.cm.magma(np.linspace(0.3, 0.8, len(top_managers)))
        bars = plt.barh(top_managers['Deal Owner Name'], top_managers['Conversion_%'], color=colors)
        plt.axvline(sales_performance['Conversion_%'].mean(), color='red', linestyle='--', linewidth=2,
                    label=f"Средняя: {sales_performance['Conversion_%'].mean():.1f}%")
        plt.title('Топ-10 менеджеров по конверсии (%)', fontsize=14, fontweight='bold')
        plt.xlabel('Конверсия (%)', fontsize=12)
        plt.legend()
        for bar in bars:
            plt.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, 
                    f'{bar.get_width():.1f}%', va='center', fontsize=9)
        plt.tight_layout()
        plt.show()
        print("✓ График 7: Эффективность менеджеров")

# 8. Распределение качества лидов (круговая диаграмма)
if 'Quality' in df_deals.columns:
    quality_counts = df_deals['Quality'].value_counts()
    if len(quality_counts) > 0:
        plt.figure(figsize=(10, 6))
        colors = ['#2ecc71', '#f39c12', '#e74c3c', '#3498db', '#9b59b6', '#1abc9c', '#e67e22']
        plt.pie(quality_counts.values, labels=quality_counts.index, autopct='%1.1f%%', colors=colors[:len(quality_counts)], startangle=90)
        plt.title('Распределение качества лидов', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.show()
        print("✓ График 8: Качество лидов")

# 9. Средняя стоимость привлечения (CAC) по каналам
if 'Source' in df_spend.columns and 'Source' in df_deals.columns:
    spend_by_source = df_spend.groupby('Source')['Spend'].sum()
    paid_by_source = df_deals[df_deals['Is_Paid'] == True].groupby('Source').size()
    cac_df = pd.DataFrame({'Spend': spend_by_source, 'Customers': paid_by_source}).fillna(0)
    cac_df['CAC'] = cac_df.apply(lambda x: x['Spend'] / x['Customers'] if x['Customers'] > 0 else 0, axis=1)
    cac_df = cac_df[cac_df['CAC'] > 0].sort_values('CAC', ascending=False).head(10).reset_index()
    
    if len(cac_df) > 0:
        plt.figure(figsize=(10, 6))
        colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(cac_df)))
        bars = plt.barh(cac_df['Source'], cac_df['CAC'], color=colors)
        plt.title('Средняя стоимость привлечения клиента (CAC) по каналам', fontsize=14, fontweight='bold')
        plt.xlabel('Евро', fontsize=12)
        plt.gca().invert_yaxis()
        for bar in bars:
            plt.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                    f'€{bar.get_width():.2f}', va='center', fontsize=9)
        plt.tight_layout()
        plt.show()
        print("✓ График 9: CAC по каналам")

# 10. Соотношение Paid vs Total сделок по источникам
if 'Source' in df_deals.columns:
    source_stats = df_deals.groupby('Source').agg(
        Total=('Id', 'count'),
        Paid=('Is_Paid', 'sum')
    ).reset_index()
    source_stats = source_stats.sort_values(by='Total', ascending=False).head(10)
    
    if len(source_stats) > 0:
        fig, ax = plt.subplots(figsize=(12, 6))
        x = np.arange(len(source_stats['Source']))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, source_stats['Total'], width, label='Всего сделок', color='steelblue', alpha=0.8)
        bars2 = ax.bar(x + width/2, source_stats['Paid'], width, label='Оплаченные', color='#2ecc71', alpha=0.8)
        
        ax.set_xlabel('Источник', fontsize=12)
        ax.set_ylabel('Количество', fontsize=12)
        ax.set_title('Соотношение всех и оплаченных сделок по источникам', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(source_stats['Source'], rotation=45, ha='right')
        ax.legend()
        
        plt.tight_layout()
        plt.show()
        print("✓ График 10: Соотношение сделок по источникам")


print("\n" + "=" * 60)
print("Пайплайн расчетов успешно выполнен. Все графики построены.")
print("=" * 60)

# 11. Визуализация конверсионной воронки бизнеса
if 'step_contacts' in locals():
    funnel_stages = ['Контакты (UA Лиды)', 'Сделки в CRM', 'Оплаты (Buyers)']
    funnel_values = [step_contacts, step_deals, step_paid]
    
    plt.figure(figsize=(10, 5))
    # Строим горизонтальный bar-chart, центрированный для эффекта воронки
    positions = np.arange(len(funnel_stages))
    max_val = funnel_values[0]
    
    # Расчет отступов слева для создания воронкообразной формы
    left_bounds = [(max_val - val) / 2 for val in funnel_values]
    
    bars = plt.barh(positions, funnel_values, left=left_bounds, color=['#34495e', '#3498db', '#2ecc71'], alpha=0.85, height=0.6)
    
    plt.yticks(positions, funnel_stages, fontsize=12, fontweight='bold')
    plt.title('Сквозная конверсионная воронка школы немецкого языка', fontsize=14, fontweight='bold', pad=20)
    plt.xlabel('Количество человек', fontsize=11)
    plt.gca().invert_yaxis() # Чтобы воронка шла сверху вниз
    
    # Добавляем подписи данных прямо внутрь воронки
    for i, bar in enumerate(bars):
        val = funnel_values[i]
        pct_of_total = (val / max_val) * 100
        text_x = left_bounds[i] + (val / 2)
        plt.text(text_x, bar.get_y() + bar.get_height()/2, f'{val:,} чел.\n({pct_of_total:.1f}%)', 
                 va='center', ha='center', color='white', fontsize=10, fontweight='bold')
                 
    plt.grid(False) # Для воронки сетка не нужна
    plt.tight_layout()
    plt.show()
    print("✓ График 11: Воронка конверсии")

input('\n📌 Нажмите Enter для выхода...')
