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

def extract_length(text):
    """Извлекает числовое значение длины из текста"""
    if not text:
        return None
        
    # Удаляем все пробелы и заменяем запятую на точку
    cleaned = text.replace(' ', '').replace(',', '.')
    
    # Ищем числа с плавающей точкой
    match = re.search(r'(\d+\.?\d*)', cleaned)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None

def parse_cable_journal_docx(docx_path, db_params, project_document_id):
    """Парсер для кабельного журнала с использованием pandas"""
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
    
    total_inserted = 0

    # Создаем список всех таблиц в виде DataFrame
    tables = []
    for table in doc.tables:
        data = []
        for row in table.rows:
            current_row = []
            for cell in row.cells:
                text = cell.text.strip()
                text = re.sub(r'\s+', ' ', text)
                current_row.append(text)
            data.append(current_row)
        
        # Создаем DataFrame и дополняем до 13 столбцов
        df = pd.DataFrame(data)
        if len(df.columns) < 13:
            for i in range(len(df.columns), 13):
                df[i] = ''
        tables.append(df)

    # Обрабатываем каждую таблицу
    for table_idx, df in enumerate(tables):
        logger.info(f"Обработка таблицы {table_idx+1}")
        
        # Определяем тип таблицы
        type1 = False
        type2 = False
        
        if not df.empty:
            first_row = df.iloc[0].tolist()
            if first_row[0] == "Номер кабеля":
                type1 = True
            elif first_row[0] == "Обозначение кабеля, провода" or first_row[0] == "Обозначение\nкабеля,\nпровода":
                type2 = True
        
        # Пропускаем таблицы неизвестного типа
        if not type1 and not type2:
            logger.info(f"Таблица {table_idx+1} неизвестного формата, пропускаем")
            continue

        # Обрабатываем строки таблицы
        for idx, row in df.iterrows():
            cells = row.tolist()
            # print(cells)
            # Пропускаем заголовки и разделители
            if (idx == 0 or 
                all(cell == cells[0] for cell in cells) or
                cells[0] in ['Номер кабеля', 'Обозначение кабеля, провода', 'Обозначение\nкабеля,\nпровода'] or
                cells == ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13']):
                continue
            
            if type1:
                cable_data = {
                    'cable_identification': cells[0],
                    'trassa_beginning': cells[2],
                    'trassa_end': cells[5],
                    'cable_or_wire_brand': cells[8],
                    'cable_or_wire_projet_length': extract_length(cells[9]),
                    'cable_or_wire_laying_brand': cells[10],
                    'cable_or_wire_laying_length': extract_length(cells[11]),
                    'note': cells[12] if len(cells) > 12 else ''
                }

                try:
                    insert_query = """
                    INSERT INTO "Cable" (
                        "ID_cable", "ID_project_document", "Cable_identification",
                        "Trassa_beginning", "Trassa_end", "Cable_or_wire_brand",
                        "Cable_or_wire_projet_length", "Cable_or_wire_laying_brand",
                        "Cable_or_wire_laying_length"
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                    data = (
                        str(uuid.uuid4()),  
                        project_document_id,
                        cable_data['cable_identification'],
                        cable_data['trassa_beginning'],
                        cable_data['trassa_end'],
                        cable_data['cable_or_wire_brand'],
                        cable_data['cable_or_wire_projet_length'],
                        cable_data['cable_or_wire_laying_brand'],
                        cable_data['cable_or_wire_laying_length']
                    )

                    cursor.execute(insert_query, data)
                    total_inserted += 1

                except Exception as e:
                    logger.error(f"Ошибка при вставке данных кабеля {cable_data['cable_identification']}: {str(e)}")
                    conn.rollback()
                    continue

            elif type2:
                cable_data = {
                    'cable_identification': cells[0],
                    'trassa_beginning': cells[1],
                    'trassa_end': cells[2],
                    'pipe_passage_designation': cells[3],
                    'pipe_passage_diameter': cells[4],
                    'pipe_passage_length': extract_length(cells[5]),
                    'draw_box_passing_length': extract_length(cells[6]),
                    'cable_or_wire_brand': cells[7],
                    'cable_or_wire_projet_cross_section': cells[8],
                    'cable_or_wire_projet_length': extract_length(cells[9]),
                    'cable_or_wire_laying_brand': cells[10],
                    'cable_or_wire_laying_cross_section': cells[11],
                    'cable_or_wire_laying_length': extract_length(cells[12])
                }

                try:
                    insert_query = """
                    INSERT INTO "Cable" (
                        "ID_cable", "ID_project_document", "Cable_identification",
                        "Trassa_beginning", "Trassa_end", "Pipe_passage_designation",
                        "Pipe_passage_diameter", "Pipe_passage_length", "Draw_box_passing_length",
                        "Cable_or_wire_brand", "Cable_or_wire_projet_cross_section", "Cable_or_wire_projet_length",
                        "Cable_or_wire_laying_brand", "Cable_or_wire_laying_cross_setion", "Cable_or_wire_laying_length"
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                    data = (
                        str(uuid.uuid4()),  
                        project_document_id,
                        cable_data['cable_identification'],
                        cable_data['trassa_beginning'],
                        cable_data['trassa_end'],
                        cable_data['pipe_passage_designation'],
                        cable_data['pipe_passage_diameter'],
                        cable_data['pipe_passage_length'],
                        cable_data['draw_box_passing_length'],
                        cable_data['cable_or_wire_brand'],
                        cable_data['cable_or_wire_projet_cross_section'],
                        cable_data['cable_or_wire_projet_length'],
                        cable_data['cable_or_wire_laying_brand'],
                        cable_data['cable_or_wire_laying_cross_section'],
                        cable_data['cable_or_wire_laying_length']
                    )

                    cursor.execute(insert_query, data)
                    total_inserted += 1

                except Exception as e:
                    logger.error(f"Ошибка при вставке данных кабеля {cable_data['cable_identification']}: {str(e)}")
                    conn.rollback()
                    continue

    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"Обработка завершена. Добавлено записей: {total_inserted}")
    return total_inserted

if __name__ == "__main__":
    docx_file_path = sys.argv[1]
    
    db_params = {
        "host": "localhost",
        "port": "5432",
        "database": "cable_db",
        "user": "postgres",
        "password": "test1"
    }
    
    project_document_id = None
    
    logger.info(f"Начата обработка файла: {docx_file_path}")
    logger.info(f"Project Document ID: {project_document_id}")
    
    try:
        record_count = parse_cable_journal_docx(docx_file_path, db_params, project_document_id)
        print(f"Обработка успешно завершена! Добавлено записей: {record_count}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        traceback.print_exc()
        sys.exit(2)