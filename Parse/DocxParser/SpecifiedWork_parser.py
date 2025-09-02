# SpecifiedWork_parser.py
from docx import Document
import os
import re
import sys
import traceback
import psycopg2
import uuid
import logging
import pandas as pd
import numpy as np

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_docx_to_specified_work(docx_path, db_params, project_document_id, document_section_id):
    """Основная функция для обработки DOCX файла и записи в таблицу SpecifiedWork"""
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        logger.info("Успешное подключение к базе данных PostgreSQL!")
    except Exception as e:
        logger.error(f"Ошибка подключения к PostgreSQL: {str(e)}")
        raise
    
    try:
        doc = Document(docx_path)
        logger.info(f"Файл {docx_path} успешно открыт")
    except Exception as e:
        conn.close()
        logger.error(f"Ошибка открытия DOCX файла: {str(e)}")
        raise

    # Создаем список всех таблиц в виде DataFrame
    tables = []
    for table in doc.tables:
        data = []
        for row in table.rows:
            current_row = []
            for cell in row.cells:
                text = cell.text.strip()
                text = re.sub(r'\s+', ' ', text)
                text = text.replace(" ,", ",")
                current_row.append(text)
            data.append(current_row)
        df_table = pd.DataFrame(data)
        tables.append(df_table)

    total_inserted = 0

    # Обрабатываем каждую таблицу
    for table_idx, df in enumerate(tables):
        logger.info(f"Обработка таблицы {table_idx+1}")
        
        # Функция для вычисления схожести столбцов
        def calculate_similarity(col1, col2):
            mask = (~df[col1].isna()) & (~df[col2].isna())
            if mask.sum() == 0:
                return 0
            matches = (df.loc[mask, col1] == df.loc[mask, col2]).sum()
            total = mask.sum()
            return (matches / total) * 100

        # Находим группы схожих столбцов
        groups = []
        current_group = [df.columns[0]]
        for i in range(1, len(df.columns)):
            similarity = calculate_similarity(df.columns[i-1], df.columns[i])
            if similarity > 80:
                current_group.append(df.columns[i])
            else:
                groups.append(current_group)
                current_group = [df.columns[i]]
        groups.append(current_group)

        # Формируем очищенный DataFrame
        columns_to_keep = []
        for group in groups:
            columns_to_keep.append(group[0])
        df_cleaned = df[columns_to_keep].copy()

        # Заменяем NaN на пустые строки
        df_cleaned = df_cleaned.fillna('')
        
        # Переименовываем столбцы в соответствии с ожидаемой структурой
        # Предполагаем, что структура: [№ п/п, Наименование, Ед. изм., Кол-во, Примечание]
        expected_columns = ['Work_identification', 'Name_work', 'Units', 'Quantity', 'Note']
        for i, col in enumerate(df_cleaned.columns):
            if i < len(expected_columns):
                df_cleaned = df_cleaned.rename(columns={col: expected_columns[i]})
            else:
                # Если столбцов больше, чем ожидалось, добавляем к примечанию
                df_cleaned[expected_columns[4]] = df_cleaned[expected_columns[4]] + ' ' + df_cleaned[col]
        
        # Оставляем только нужные столбцы (обрезаем до 5)
        df_cleaned = df_cleaned[expected_columns[:min(len(df_cleaned.columns), 5)]]

        try:
            inserted_count = 0
            for idx, row in df_cleaned.iterrows():
                # Пропускаем заголовки и разделители
                if idx < 2 or not re.match(r'^\d+\.\d+(\.\d+)*$', str(row.get('Work_identification', ''))):
                    continue
                
                # Извлекаем данные из строки
                work_identification = row.get('Work_identification', '')
                name_work = row.get('Name_work', '')
                units = row.get('Units', '')
                quantity = row.get('Quantity', '')
                note = row.get('Note', '')
                
                # Обработка единиц измерения (может быть составной, например "м/шт")
                units_parts = str(units).split('/')
                units1 = units_parts[0].strip() if units_parts and units_parts[0].strip() else None
                units2 = units_parts[1].strip() if len(units_parts) > 1 and units_parts[1].strip() else None
                
                # Обработка количества (может быть составным, например "1482/494")
                quantity_parts = str(quantity).split('/')
                quantity1 = None
                quantity2 = None
                
                try:
                    if quantity_parts and quantity_parts[0].strip():
                        quantity1 = float(quantity_parts[0].replace(',', '.').strip())
                    if len(quantity_parts) > 1 and quantity_parts[1].strip():
                        quantity2 = float(quantity_parts[1].replace(',', '.').strip())
                except ValueError:
                    logger.warning(f"Не удалось преобразовать количество: {quantity}")
                
                # Генерируем UUID для работы
                work_id = str(uuid.uuid4())
                
                # Формируем запрос
                insert_query = '''
                INSERT INTO "SpecifiedWork" (
                    "ID_work",
                    "ID_project_document",
                    "ID_document_section",
                    "Work_identification",
                    "Name_work",
                    "Units1",
                    "Units2",
                    "Quantity1",
                    "Quantity2",
                    "Note"
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                '''
                
                # Параметры для запроса
                data = (
                    work_id,
                    project_document_id,
                    document_section_id,
                    work_identification,
                    name_work,
                    units1,
                    units2,
                    quantity1,
                    quantity2,
                    note
                )
                
                # Выполняем запрос
                cursor.execute(insert_query, data)
                inserted_count += 1
            
            # Фиксируем изменения для таблицы
            conn.commit()
            total_inserted += inserted_count
            logger.info(f"Таблица {table_idx+1}: добавлено {inserted_count} записей")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке таблицы {table_idx+1}: {str(e)}")
            conn.rollback()
            traceback.print_exc()
                
    cursor.close()
    conn.close()
    logger.info(f"Обработка завершена. Всего добавлено записей: {total_inserted}")
    return total_inserted

if __name__ == "__main__":
    docx_file_path = sys.argv[1]
    if len(sys.argv) < 3:
        project_document_id = ""
        document_section_id = ""
    else:
        project_document_id = sys.argv[2]
        document_section_id = sys.argv[3]
    
    db_params = {
        "host": "localhost",
        "port": "5432",
        "database": "cable_db",
        "user": "postgres",
        "password": "test1"
    }
    
    logger.info(f"Начата обработка файла: {docx_file_path}")
    
    try:
        record_count = parse_docx_to_specified_work(
            docx_file_path, 
            db_params, 
            project_document_id, 
            document_section_id
        )
        print(f"Обработка успешно завершена! Добавлено записей: {record_count}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        traceback.print_exc()
        sys.exit(2)